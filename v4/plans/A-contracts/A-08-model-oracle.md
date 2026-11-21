# A-08 — Model oracle, 3.x side

| Field | Value |
|---|---|
| Status | `done` |
| Story | A — Contracts & baselines |
| Target branch | `dev-3.x` (merged forward to `dev-4.x`, PD-12) |
| Depends on | [A-04](A-04-pinned-corpus.md), [A-07](A-07-differential-framework.md) |
| Blocks | [3x-08](../3x-quick-wins/3x-08-butcher-literal-tags.md), [3x-18](../3x-quick-wins/3x-18-unknown-union-fallback.md), [B-13](../B-spike/B-13-gate-run-and-decision.md) |
| Gate-conditional | no |
| Decisions | R05, R06, R26, D84–D87, D91–D95, D105–D108 (as the approved differences 4.0 will claim) |
| Sources | [01 §3.6–3.7](../../research/01-models.md), [10 Layers 1–3](../../research/10-forward-compatibility.md), [19 D105–D108, R06](../../research/19-review-resolutions.md), [codex-review R05, R06, §11](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The B spike and the C emitters replace the pydantic models. An independent record of what 3.x models *do* on every
corpus input is needed. That covers more than happy-path JSON: R26 asks for constructors, `replace`, aliases,
defaults and Unknown paths. The codex §11 probes established 3.x facts such as "equality across bots is false",
"`model_extra` holds only unknown fields" and "`model_dump_json()` returns `str`". They must become replayable cases.

## Scope

**In:** `differential/sides/aiogram3/model.py` and its manifest entries. For each A-04 wire input (decode and
forward-compat kinds), the probes are:

| Probe | Records |
|---|---|
| `decode.json` | `Update.model_validate_json(bytes, context={"bot": bot})` → ok or error (type + `error_count`) |
| `decode.dict` | `json.loads` + `model_validate` (the webhook path), same record |
| `dump.python` | `model_dump(mode="json", exclude_unset=True)` (Python names) |
| `dump.wire` | `model_dump(mode="json", by_alias=True, exclude_unset=True)` |
| `dump_json.default` | `model_dump_json()`: type (`str`) and value |
| `event` | `update.event_type` and the type name of `update.event` |
| `access` | a fixed list of attribute paths per input (e.g. `message.text`, `message.from_user.id`, `message.chat.type`, `message.entities[0].type`) |
| `extra` | `model_extra` on the root and nested objects |
| `eq` | the same payload decoded twice, with the same bot and with two different bots → `==` |
| `hash` | `hash(obj)` → value class or `TypeError` |
| `pickle` | an unbound object round-trips; a bound object fails (3.x behaviour, 19 header) |
| `copy` | `model_copy(update={...})` for one field, including whether it validates (3.x doesn't) |
| `construct` | for a fixed list of types (User, Chat, Message, InlineKeyboardMarkup, SendMessage), constructor kwargs → `model_dump`. Covers aliases (`from_user` vs `from`) and `Default(...)` placeholders |
| `mutate` | for `MutableTelegramObject` types: attribute assignment works (3.x) |

- The **forward-compat** inputs fail on 3.x. That is recorded as an error, and the manifest classes them `new`
  (decision D10 / D107).
- Write manifest entries for the known 4.0 differences with narrow comparators:
  - `dump_json.default` keys are wire names: D86 / D94;
  - `eq` across bots is true in 4.0: D108;
  - `hash`: D108 / D106;
  - `mutate` raises in 4.0: D15;
  - `extra` extras must be JSON-shaped: D87;
  - `copy` validates: R06.

  All are `gate = true` where the decision is gate-dependent.
- Poison support: with `--poison`, the adapter drops one field from every `dump.*` record.

**Out:**
- The 4.0 adapter: B plans (B-06 / B-13).
- Request encoding: A-09.

## Checklist

- [ ] Implement the probes. Use a bot built with a fake token, so no network is needed. Make the access-path list
      data-driven: a `[access]` table per input in the manifest or a sidecar file.
- [ ] Run `differential run --kind model --left pypi:aiogram==3.32.0 --right path:.` on the current `dev-3.x`:
      0 mismatches.
- [ ] Run with `--poison right`: mismatches detected.
- [ ] Encode the codex §11 probes as named cases. Each must reproduce the recorded observation; if one doesn't, write
      it in Notes.
- [ ] Add the manifest entries above.
- [ ] Changelog: none. Use the `skip news` label.

## Acceptance criteria

- The oracle covers every A-04 decode and forward-compat input with every probe that applies.
- 3.32.0 vs `dev-3.x` HEAD: 0 unapproved mismatches.
- Poison detected.
- The codex §11 model probes (equality across bots false, `model_extra` only unknown, `model_dump_json` is `str`,
  nested null survives `exclude_none`, pickling a bound object fails) are reproduced as recorded cases.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Only happy-path decode and dump | Misses constructors, aliases, defaults and Unknown paths | R26 |
| Generate expected values from the IR | Not independent | R26 |

## Validation

```bash
uv run python -m differential run --kind model --left pypi:aiogram==3.32.0 --right path:.
uv run python -m differential run --kind model --left pypi:aiogram==3.32.0 --right path:. --poison right; test $? -ne 0
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
```

## Workflow notes

- **Outputs:** the 3.x model trace and its approved-difference entries, used by B-13 (spike correctness alongside
  speed), the C exit gate (C-25) and 3x-08 / 3x-18 (3.x invariance).
- 4.0 adapters must implement the same probe names.

## Notes
