# 3x-16 — Redis one-round-trip `update_data` (dropped)

| Field | Value |
|---|---|
| Status | `dropped` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | — |
| Blocks | — |
| Gate-conditional | no |
| Decisions | PD-28, D113, D120 |
| Sources | [09 #18](../../research/09-3x-quick-wins.md), [04 §4](../../research/04-fsm.md), [19 D113](../../research/19-review-resolutions.md) |
| Size | — |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

09 #18 proposed making `RedisStorage.update_data` one round trip with Lua or a pipeline.

## Scope

**In:** nothing. **Out:** everything. The item is dropped.

## Checklist

- [ ] None.

## Acceptance criteria

- None.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Pipeline `update_data` | A pipeline alone isn't an atomic read/merge/write | D120, R27 |
| Lua `update_data` | Lua can't run user codec hooks (`json_loads` / `json_dumps`) | D120, D113 |
| A perf-motivated rewrite at all | The real issue is atomicity, fixed separately on 3.x with a `WATCH`/`MULTI` transaction, which adds round trips | PD-28 |

## Validation

None.

## Workflow notes

- The atomicity fix is a separate 3.x change (FSM storage atomicity), not a plan.
- In 4.0, F-06 keeps the 3.x key layout with a pipelined state+data read, and atomicity comes from isolation (D113).

## Notes

Dropped by PD-28 (2026-11-17): "09 #18 dropped (atomicity is a separate 3.x fix)".
