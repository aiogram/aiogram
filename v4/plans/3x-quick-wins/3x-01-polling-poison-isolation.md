# 3x-01 — Polling: isolate poison updates instead of stalling

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-03](../A-contracts/A-03-poison-update-decision.md) (owner-signed decision record), [A-05](../A-contracts/A-05-bench-harness.md) (own-baseline measurement) |
| Blocks | [A-06](../A-contracts/A-06-record-3x-baselines.md), [3x-18](3x-18-unknown-union-fallback.md) |
| Gate-conditional | no |
| Decisions | D10 (3.x mitigation), D120, R13, R27, PD-28, PD-29 |
| Sources | [09 #21](../../research/09-3x-quick-wins.md), [10 §5](../../research/10-forward-compatibility.md), [10 Layer 2](../../research/10-forward-compatibility.md), [19 R13](../../research/19-review-resolutions.md), [A-03](../A-contracts/A-03-poison-update-decision.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

One update that 3.x can't validate (for example, an unknown union tag after a Bot API release) makes the whole
`getUpdates` batch raise `ClientDecodeError`. `Dispatcher._listen_updates` treats that as a network failure, backs
off and asks for the same batch again, so polling **stalls forever** (reproduced; public issues #1840 / #1890).
Ride-along: `ok: true` with `result: null` raises `TypeError` inside polling.

The webhook background-task drain is an external prerequisite, not part of any plan. [3x-19](3x-19-token-leak-fix.md) touches
the same client code; if it has to ship before A-03 is signed off, it ships on its own and this plan rebases.

## Scope

**In** (shape fixed by A-03 and PD-28: "per-update decode only when the batch fails"):
- The fast path stays unchanged: `bot(GetUpdates)` validates the whole response with `model_validate_json`. The
  slower variant in 09 #21 (always decode the raw list and validate each update) is rejected; see *Rejected
  alternatives*.
- On `ClientDecodeError` from `GetUpdates` in `Dispatcher._listen_updates` (`aiogram/dispatcher/dispatcher.py`):
  1. Parse `e.data` (the raw response text kept by `ClientDecodeError`) with `json.loads`.
  2. Take `result` as a list and validate each element as `Update` separately, with `context={"bot": bot}`.
  3. Yield the good updates in order.
  4. For each bad one, log, report it as A-03 decides, and **confirm its offset** (`offset = update_id + 1`).
- When an element has no readable `update_id`, or the body isn't a JSON object with a list `result`, use the
  `limit=1` fallback from A-03: repeat `GetUpdates(limit=1, offset=current)` to isolate the single bad update. If
  even that can't produce an `update_id`, keep today's backoff and retry, and log at `ERROR`.
- `BaseSession.check_response` (`aiogram/client/session/base.py`): when `ok` is true and `result` is missing or
  `None` for a method whose return type isn't optional, raise `ClientDecodeError` instead of failing later with a
  `TypeError`.
- `ClientDecodeError` and the response read: decode the body with `errors="replace"`. `__str__` no longer embeds the
  whole `Content:` payload, so the log line stays bounded. Keep `.data` with the content; PD-29 adds `.raw` in 4.0
  and is out of scope here.
- Docs: polling page section "Undecodable updates": the behaviour, best-effort delivery (R13) and the data-loss
  trade-off.

**Out:**
- Webhook poison updates: [3x-02](3x-02-webhook-poison-200.md).
- `Unknown` union variants that avoid the failure altogether: [3x-18](3x-18-unknown-union-fallback.md), optional.
- 4.0 Layer 2 (`router.unknown_update`, `phase=DECODE`): E-14 and D-09.

## Checklist

- [ ] Read A-03 and confirm it is signed off. If it isn't, stop and set `Status: blocked`.
- [ ] Measure the baseline with A-05: `response.getUpdates.100` decode through `bot(GetUpdates)`, before and after.
      The happy path must not regress.
- [ ] Implement the failure path in `_listen_updates` as above. Keep the backoff logic for real network errors
      unchanged.
- [ ] Report bad updates exactly as A-03 specifies: log level, logger `aiogram.dispatcher`, no payload body at
      default level, and the `errors` observer behaviour.
- [ ] The `ok`-without-`result` check in `check_response`; update the ~7 tests that mock `result=None` (they relied on the bug).
- [ ] Bound `ClientDecodeError.__str__` and use `errors="replace"`.
- [ ] Tests:
  - a batch with one update carrying an unknown `ChatMember` status tag: the other updates are dispatched in order,
    the offset advances past the bad one, and it is reported once;
  - a batch whose bad element lacks `update_id`: the `limit=1` fallback runs;
  - an envelope that isn't JSON: backoff as today;
  - `ok` with `result=None`.

  Use a fake session as in `tests/mocked_bot.py`.
- [ ] 100% coverage of the changed code.
- [ ] Changelog fragment `CHANGES/<pr>.bugfix.rst`:
  - describe the behaviour change: bad updates are skipped and reported, not retried;
  - credit the reporter per the repository's convention (fragment and `Reported-by:` commit trailer).
- [ ] Migration registry: no entry. This is a 3.x behaviour change, not a 4.0 migration item; 4.0's own behaviour is
      breaking change 9, owned by E/D.

## Acceptance criteria

- With `tests/` fixtures, a 3-update batch whose middle update has an unknown union tag dispatches updates 1 and 3,
  confirms all three offsets, and doesn't call `GetUpdates` with the same offset again.
- No stalling: the next `GetUpdates` call carries `offset = last_update_id + 1`.
- A-05 `compare`, `response.getUpdates.100` happy path: median within noise (≤ +2%) of the parent commit.
- `ClientDecodeError` text is ≤ 1 KB for a 1 MB body.
- The release goes into a 3.x **minor** (PD-28), because skipping updates is a behaviour change.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Always decode `getUpdates` as a raw list and validate each `Update` (09 #21 wording) | `json.loads` + `model_validate` costs 101 µs vs 84 µs for `model_validate_json` per update (01 §1), which would also bias the "optimised 3.x" baseline in A-06 | PD-28 |
| Keep retrying the same batch | That is the bug | D10 |
| Advance past the whole batch | Loses good updates too | R13 |
| New exception class `TelegramDecodeError` | No new exception classes; `ClientDecodeError` is kept | PD-29, D47 |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing   # coverage must stay 100%
make lint
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases response.getUpdates.100   # A-05 CLI
```

## Workflow notes

- Consumes the A-03 decision and the A-05 harness. Its result is part of the "optimised 3.x" tag (A-06).
- The polling tests and design inform E-15 (Poller) and D-09 (response decoder): they are the 3.x behaviour that 4.0
  generalises.
- Can run in parallel with every 3x plan except 3x-19, which touches the same client code.

## Notes
