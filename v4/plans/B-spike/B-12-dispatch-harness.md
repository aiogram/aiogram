# B-12 — End-to-end dispatch harness

| Field | Value |
|---|---|
| Status | `todo` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-00](B-00-freeze-gate-spec.md), [B-02](B-02-bench-adapter-memory-estimator.md), [B-05](B-05-views-cache-gc-routing-keys.md), [B-07](B-07-bound-views.md), [B-09](B-09-sendmessage-encoder-response.md), [A-06](../A-contracts/A-06-record-3x-baselines.md), [A-10](../A-contracts/A-10-routing-oracle.md) |
| Blocks | [B-13](B-13-gate-run-and-decision.md) |
| Gate-conditional | no |
| Decisions | D26, D103, B14, PD-03 |
| Sources | [01-models.md §5 item 4](../../research/01-models.md), [13-aiogram-rust-review.md §1 (routing), §5](../../research/13-aiogram-rust-review.md), [03-routing.md §3](../../research/03-routing.md), [09-3x-quick-wins.md #1, #11–#13](../../research/09-3x-quick-wins.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D26 loosened warm access to ≤1.6× on the condition that **end-to-end dispatch on a realistic router is no slower**
than optimised 3.x. aiogram_rust's Python routing over native objects was 13% slower than 3.x (13 §1). This task
builds that measurement so it measures **the model layer only**:
- the same 3.x dispatcher code runs on both sides;
- there are no compiled rejectors;
- there is no dependency on E.

## Scope

**In:**
- **Harness.** A bench-only dispatch harness next to the B-02 adapter (default `benchmarks/b_gate/dispatch/`). It runs
  `aiogram.Dispatcher` from the **optimised-3.x tag (A-06)** on both sides with the pinned realistic router from A-10.
- **3.x side.** Updates decoded with `Update.model_validate_json(raw, context={"bot": bot})`, then
  `await dp.feed_update(bot, update)`.
- **Native side.** Updates decoded with `_core.decode_update(raw, bot=bot)`, then the same `dp.feed_update`. The
  native side gets only the minimal shims that make 3.x code accept native objects:
  - ABC registration of the native classes on the 3.x pydantic classes. pydantic's `ModelMetaclass` derives from
    `ABCMeta`, so `aiogram.types.Update.register(_core.Update)` etc. makes the `isinstance(event, Update)` in
    `UserContextMiddleware.__call__` and the `InaccessibleMessage` checks in `resolve_event_context`
    (`aiogram/dispatcher/middlewares/user_context.py`) work unchanged.
  - Updates arrive already bound, so the `update.bot != bot` round-trip in `Dispatcher.feed_update` never runs on
    either side.
- **Handlers.** They read the typical fields a real handler reads (`message.text`, `from_user.id`, `chat.id`, one
  entity), so user-code attribute cost is included (D26 trade-off), and return without an API call.
- **Measurement.** Per-update time across first / middle / last / unmatched matching positions (codex §10 dispatch
  list), FSM on and off, through the B-02 protocol.
- **Informational variant.** The native side additionally pre-computes `update.routing_keys()` once per update and
  passes nothing else, to measure its cost. Not gated.

**Out:**
- Compiled rejectors, the routing snapshot and the `routing_keys()` consumers (E-02, E-09); E-21 measures routing
  gains.
- Changes to 3.x dispatcher code (the shims live in the harness only).
- Error / unknown-update paths beyond what the 3.x dispatcher supports.

## Checklist

- [ ] Check that the in-tree 3.x package on `dev-4.x` matches the A-06 optimised-3.x tag for `aiogram/dispatcher/`,
  `aiogram/filters/`, `aiogram/fsm/` and `aiogram/types/` (diff against the tag; A-01 sync policy). If it differs, stop
  and sync first. Both sides must run in one process so the ABC shims apply.
- [ ] Load the A-10 realistic router and the A-04 update mix named in `gate.toml`.
- [ ] Implement both sides with the same `Dispatcher` instance factory; assert both sides produce identical handler
  outcomes (which handler ran, returned value type) for every update in the mix. The A-10 routing oracle can be
  reused.
- [ ] ABC-registration shims for every spike class on its 3.x pydantic twin; nothing in `aiogram/` is modified.
- [ ] Decide what to do if the A-10 realistic router's handlers call the API (proposed default: replace those calls
  with attribute reads of the same fields for the gate run, since encode is measured separately by B-09, and record
  the substitution in the run record). Record in Notes and flag to owner.
- [ ] Decide whether outer middlewares from the realistic router stay (proposed default: yes, as in the A-10
  definition; they run identically on both sides). Record and flag.
- [ ] Register the gated dispatch workload and the informational `routing_keys()` variant in the B-02 adapter.
- [ ] Tests: a pytest that runs 100 updates through both sides and asserts outcome equality (100% of new Python).
- [ ] No changelog or registry entry (bench only).

## Acceptance criteria

- Both sides produce identical handler outcomes for 100% of the pinned update mix.
- The gated dispatch workload runs on Linux (+uvloop) and macOS through the B-02 protocol and emits a result JSON with
  per-position timings.
- This task's PR changes nothing under `aiogram/` (shims live in the harness).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Compiled rejectors over `routing_keys()` on the native side only | Credits routing gains to the model layer; E measures them | B-00, E-09 |
| Waiting for E's compiled snapshot | Puts E on the binding gate's critical path | codex §9, D121 |
| Patching the 3.x dispatcher for native types | Changes the code under test on one side | B-00 |
| Empty handlers | Hide the warm-access trade-off that D26 accepted | D26, 13 §5 |

## Validation

```bash
make bench
uv run pytest tests/test_core/test_dispatch_harness.py
uv run python -m benchmarks compare --base v4-baseline/3.x-optimised --head WORKTREE --cases routing.52-handlers,routing.5routers-30handlers
make lint
```

## Workflow notes

- Inputs: the A-06 optimised-3.x tag; the A-10 realistic router and routing oracle; A-04 updates; B-05 / B-07
  views; B-09 for the bound decode; the B-02 adapter.
- Outputs: the gated dispatch result for B-13; the `routing_keys()` cost number for E-09.

## Notes
