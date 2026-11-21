# E-23 — Runner bot registry: `add_bot` / `remove_bot`, `bot_added` / `bot_removed`, shared-FSM ownership

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-13](E-13-runner-lifecycle-bot-registry.md), [E-12](E-12-runtime-errors.md) |
| Blocks | [E-16](E-16-webhook-core-aiohttp-sources.md), [E-19](E-19-multi-runner-free-threading-sharding.md), [G-16](../G-features/G-16-cli-run.md), [H-14](../H-testing-observability/H-14-delivery-through-runner.md), [H-08](../H-testing-observability/H-08-otel-traces.md), [E-21](E-21-e-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D21, D22, R11, R12, R13 |
| Sources | [12-runtime.md §1–§4, §8](../../research/12-runtime.md), [19 R12, R13](../../research/19-review-resolutions.md), [codex-review R11, R12](../../research/codex-review.md), [07-free-threading.md §1](../../research/07-free-threading.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

In 3.x the bots are fixed when `start_polling(*bots)` starts, and `bots` in handler data exists only for polling. D21
gives the Runner a bot registry so bots can be added and removed at runtime (`TokenBasedRequestHandler` creates bots
on demand), with lifecycle events for every bot. E-13 owns the Runner state machine; this plan owns the registry that
plugs into its hook points, and the ownership of resources several Runners share.

## Scope

**In:**
- **Bot registry:** ordered, read-only; `runner.add_bot(bot, source=..., close_session=True)` and
  `runner.remove_bot(bot)`; `bots` in startup/handler data is a cached tuple rebuilt on add/remove.
- **Events:** `dp.bot_added` / `dp.bot_removed` observers fire for every bot, including those present at start (after
  `startup`, before `shutdown`), through E-13's "announce initial bots" / "de-announce bots" hook points and on
  start-up rollback. `close_session=True` default closes the bot session on removal/stop (3.x `close_bot_session`).
- Failures in `bot_added` / `bot_removed` handlers go to `runtime_errors` (E-12) with the E-11 runtime phase
  `BOT_HOOK`.
- `runner.detach(source)` (E-13) removes that source's bots through the registry.
- **Shared-FSM ownership across Runners:** 3.x registers `self.fsm.close` on `dp.shutdown`, so with several Runners on
  one Dispatcher (E-19) the first Runner to stop would close the shared storage. See the Decide item.
- Registry fault-injection tests (exception and cancellation in each `bot_added` / `bot_removed`).

**Out:**
- The Runner state machine, signals, task set, admission and the per-update context (E-13).
- Sources that call `add_bot` (E-16 `TokenBasedRequestHandler`, G-16 CLI, H-14 `WorldSource`).

## Checklist

- [ ] Registry + cached `bots` tuple; `add_bot` / `remove_bot`; `close_session`.
- [ ] `bot_added` / `bot_removed` through E-13's hook points, including rollback.
- [ ] Decide concurrent `add_bot` / `remove_bot` of the same bot (proposed default: operations on one bot id are
  serialised by a per-bot lock; `add_bot` of an already registered bot raises `ValueError`; `remove_bot` of an unknown
  bot raises `LookupError`) — record in Notes and flag to owner.
- [ ] Decide duplicate token identities (two `Bot` objects, same token) (proposed default: registry keyed by `bot.id`;
  a second `Bot` with the same id raises `ValueError`) — record in Notes and flag to owner.
- [ ] Decide a failing `bot_added` hook (proposed default: reported to `runtime_errors` with `phase=BOT_HOOK`; the
  bot stays registered and its source is started) — record in Notes and flag to owner.
- [ ] Decide whether one bot may belong to several sources (proposed default: no; one source per bot per Runner,
  `ValueError` otherwise) — record in Notes and flag to owner.
- [ ] Decide ownership of shared resources when several Runners share one Dispatcher (proposed default: remove
  `fsm.close` from `dp.shutdown`; the Dispatcher counts active Runners and closes the FSM storage when the last one
  stops; user `startup`/`shutdown` hooks run per Runner, documented) — record in Notes and flag to owner.
- [ ] Docs: the registry and multi-bot sections of the "Runner & update sources" page (E-13 writes the page).
- [ ] Migration-registry entry (PD-13) for `bots` becoming a tuple in data (3.x typed it `list[Bot]`, polling only) if
  E-20 keeps the tuple.
- [ ] Changelog fragment (`feature`).
- [ ] Tests (100% coverage), including fault injection in every `bot_added` / `bot_removed`.

## Acceptance criteria

- Fault-injection matrix: an exception or cancellation in each `bot_added` and each `bot_removed` leaves the Runner
  `closed` with no pending tasks, no unclosed owned sessions, and the expected `runtime_errors` events.
- `bot_added` fires once per bot, for bots present at start and for bots added later; `bot_removed` fires once per bot
  on removal or stop.
- `bots` seen by a handler equals the registry at the time the update was admitted.
- Two Runners over one Dispatcher: stopping the first leaves the shared FSM storage open; stopping the last closes it
  exactly once.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Bots fixed at start (3.x) | `TokenBasedRequestHandler` creates bots on demand; runtime add/remove requested | D21 |
| Move semantics (hand-off between processes, polling↔webhook switch) | Not requested | D22 |
| `fsm.close` on every Runner's shutdown (3.x) | The first Runner to stop closes storage the others still use | R11 |

## Validation

```bash
make dev
uv run pytest tests/test_runner -q
uv run pytest tests -q
make lint
uv run mypy aiogram
```

## Workflow notes

- Inputs: E-13 (state machine and hook points), E-12 (`emit_runtime_error`).
- Outputs: the registry used by E-16 (`TokenBasedRequestHandler` → `add_bot`), E-19 (multi-bot mode), G-16 (CLI),
  H-08 (`bot_added`), H-14 (`WorldSource`); the `bots` tuple type that E-20 documents.

## Notes
