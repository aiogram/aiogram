# A-10 — Routing oracle, 3.x side

| Field | Value |
|---|---|
| Status | `todo` |
| Story | A — Contracts & baselines |
| Target branch | `dev-3.x` (merged forward to `dev-4.x`, PD-12) |
| Depends on | [A-04](A-04-pinned-corpus.md), [A-07](A-07-differential-framework.md) |
| Blocks | [3x-03](../3x-quick-wins/3x-03-magicfilter-inline.md), [3x-11](../3x-quick-wins/3x-11-prebuilt-middleware-chains.md), 3x-15 (held back), [E-02](../E-runtime/E-02-dispatch-table-executor.md), [E-21](../E-runtime/E-21-e-exit-gate.md), [B-12](../B-spike/B-12-dispatch-harness.md) |
| Gate-conditional | no |
| Decisions | D114, R09, R10, R26, D111, PD-19, D48, D34, D28/D110, D12, breaking change 13 |
| Sources | [03 §1, §3, §5](../../research/03-routing.md), [19 R09, D111, D114](../../research/19-review-resolutions.md), [codex-review R09, R10, §11](../../research/codex-review.md), [README breaking changes 4, 13, 15–17, 24](../../research/README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

4.0 replaces the recursive 3.x routing (`Router.propagate_event` → `TelegramEventObserver.trigger` →
`HandlerObject.check`) with compiled per-Runner snapshots (E-02 / E-03). That rewrite must keep 3.x semantics
**except** for the decided breaks. Codex: "optimize only after the semantic oracle exists". It applies to the 3.x
quick wins too (3x-03, 3x-11).

The oracle is the external 3.x venv (PD-12). Each scenario's trace records **what ran, in what order, and what data
it saw**.

## Scope

**In:** `differential/sides/aiogram3/routing.py` and its manifest:
- **Scenario builder:** turns an A-04 `routing/*.toml` topology into a 3.x `Dispatcher` and router tree with
  *instrumented* components:
  - filters (sync, async, `F` magic, `Command`, dict-returning, raising);
  - outer and inner middlewares per router (pass, short-circuit, call-twice, data-writing, event-replacing);
  - handlers (async and sync, returning values, `SkipHandler`, raising).
- **Feeding:** events through `dp.feed_update(bot, update)` with a fake session (no network) and through
  `feed_webhook_update` for the reply-returning cases.
- **Trace per update:** the ordered list of `{component, kind, router, result}` plus the **data keys and values
  visible** at each component, as a canonical subset (exclude objects, record the type names). Also the handler
  return value / `UNHANDLED`, `errors` observer invocations (which router), and exceptions escaping `feed_update`.
- **Scenarios** in A-04 `routing/` (add the missing ones there):

| Scenario | Covers |
|---|---|
| R09 scopes | Codex §11 probes: data returned by a failed candidate's filter isn't visible to the next candidate; filter data after `SkipHandler` is visible; an inner-middleware write followed by `SkipHandler` is visible |
| Outer middlewares on routers without a match | D111 / PD-19: 4.0 skips them |
| Middleware that replaces the event | D111: 4.0 routing keys don't change |
| User filter before a `Command` / `F.x == lit` that is certainly false | Breaking change 13: 4.0 skips the user filter |
| Error raised in a nested router, `errors` handler on a sibling / parent / dispatcher | D48 bubbling |
| Sync filter doing work | D34: inline vs thread (`thread_ident` recorded) |
| Two updates with the same FSM key, the first handler awaiting | D28 / D110: the 3.x default is `DisabledEventIsolation` (they interleave); 4.0 serialises them |
| Handler requesting `event_from_user` | D12 |
| Router / middleware registered while handling | D114: 4.0 applies on refresh only |
| Flags, `get_flag`, `Filter.update_handler_flags` | D57 / D58 invariant |
| Scenes: enter / leave / back, actions by update type | D33 invariant |
| The A-04 bench topologies (52 handlers, 20 × `F.text`, 100 commands, 5 routers / 30 handlers) | invariant |

- **Manifest:** approved differences for the 4.0 decisions above (D111 / PD-19, breaking change 13, D48, D34, D28 /
  D110, D114, D12), each with a narrow comparator; everything else invariant.
- **Poison:** with `--poison`, the adapter swaps the order of two handlers in every router.

**Out:**
- The 4.0 adapter: E-21 (E exit gate).
- Lifecycle, Runner, bot registry and multi-Runner behaviour: E-13 / E-23 / E-19 / E-22.

## Checklist

- [ ] Instrumentation primitives that are standalone (stdlib + aiogram only) and record into a per-update list
      (ContextVar).
- [ ] Topology TOML → builder, covering every component kind above.
- [ ] Add the scenarios to A-04 (`routing/*.toml`, with manifest hashes).
- [ ] Run `pypi:aiogram==3.32.0` vs `path:.`: 0 mismatches. Run `--poison right`: detected.
- [ ] Reproduce the codex §11 R09 probes using the **real** `Router.message` observer. Codex discarded one probe for
      using a standalone observer.
- [ ] Manifest entries above.
- [ ] Changelog: none. Use the `skip news` label.

## Acceptance criteria

- Every scenario in the table produces a trace. 3.32.0 vs HEAD: 0 unapproved mismatches. Poison is detected.
- The R09 probes reproduce the recorded codex §11 observations.
- Against 3x-03's branch: no mismatch except the timing / thread fields, which are tagged.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep the 3.x recursive path inside 4.0 as a reference mode | The oracle is external | PD-12 |
| Assert only "same handler chosen" | Misses data scopes and middleware visibility | R09, R26 |

## Validation

```bash
uv run python -m differential run --kind routing --left pypi:aiogram==3.32.0 --right path:.
uv run python -m differential run --kind routing --left pypi:aiogram==3.32.0 --right path:. --poison right; test $? -ne 0
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
```

## Workflow notes

- **Outputs:** the routing scenarios and 3.x traces. E-02 develops against them, and E-21 (the E exit gate) runs the
  4.0 adapter with the approved differences filled in.
- 3x-03, 3x-11 and 3x-15 use it as their invariance check.

## Notes
