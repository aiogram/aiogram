# F-12 — aiogram types inside FSM data; opt-in core JSON codec for storages

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-09](F-09-fsmdata-typed-fsmcontext.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [B-06](../B-spike/B-06-value-semantics-native-api.md), [D-07](../D-client/D-07-rust-encoder-json.md) |
| Blocks | [F-17](F-17-fsm-docs-migration-page.md) |
| Gate-conditional | yes *(needs native `to_dict` / `from_dict`, D91, conditional per D104)* |
| Decisions | D30, D91, D104, PD-22 |
| Sources | [04-fsm.md §3 last bullet, §7 Model](../../research/04-fsm.md), [01-models.md §3.7](../../research/01-models.md), [11-removals.md §4 serialization.py](../../research/11-removals.md), [plans README §1 PD-22](../README.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

04 §7: `FSMData` fields may be aiogram types, stored through the core encoder as wire JSON and decoded back with
`from_dict` (D91). 04 §3 also proposed making the Rust encoder the default `json_dumps` of storages; PD-22 revises
that: **stdlib `json` stays the default**, the core encoder is **opt-in**, so stored bytes and 3.x/4.x rolling
deployments are unaffected.

## Scope

**In:**
- Register a converter with the F-08 extension hook for aiogram type classes (and registered subclasses, D83):
  dump = `obj.to_dict()` (wire shape), load = `Type.from_dict(data)` (unbound; no `bot=`). Unions (e.g.
  `MaybeInaccessibleMessage`) decode through the generated union decoder, `Unknown…` members included (D107).
- Opt-in codec helpers in `aiogram.fsm.storage.codecs` (name may change): `core_json_dumps` / `core_json_loads`
  that encode aiogram types inside plain dicts via the core encoder, usable as
  `RedisStorage(..., json_dumps=core_json_dumps)`. Output stays standard JSON (readable by `json.loads`), returns
  `str` as `RedisStorage` expects.
- Docs: storing aiogram types in typed data vs the dict API; why the default codec stays stdlib.

**Out:**
- Changing any storage default (PD-22).
- `utils/serialization.py` rewrite: owned by the model/client stories (11 §4).

## Checklist

- [ ] aiogram-type converter on the F-08 hook.
- [ ] Opt-in codec helpers.
- [ ] Tests: `FSMData` with a `Message` and a `User` field round-trips on Memory and the Redis mock; the stored value
      equals `to_dict()` output; opt-in codec output parses with `json.loads`; default `RedisStorage` still uses
      `json.dumps` (identity check).
- [ ] Tests (100% coverage of new code)
- [ ] Changelog fragment in `CHANGES/`.

## Acceptance criteria

- Round trip of the pinned A-04 corpus `Message` sample through `FSMData` gives an object equal (D84/D108) to the
  original.
- `RedisStorage().json_dumps is json.dumps`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Rust encoder as the default storage codec | Changes stored bytes; ties the default to the gate | PD-22 (revises 04 §3) |
| Pickle aiogram types into storage | Not JSON-shaped; unsafe to load; breaks Redis/Mongo parity | 04 §7 |

## Validation

```bash
make dev                                   # Rust core with native types required
cargo test
uv run pytest tests/test_fsm -q
uv run pytest tests
make lint
```

## Workflow notes

- Runs after B-13 go and once B-06 (native API) and D-07 (encoder) are done.

## Notes
