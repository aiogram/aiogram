# <ID> — <Title>

| Field | Value |
|---|---|
| Status | `todo` |
| Story | <letter> — <story name> |
| Target branch | `dev-4.x` *(or `dev-3.x` for the 3.x track)* |
| Depends on | <IDs, or "—"> |
| Blocks | <IDs, or "—"> |
| Gate-conditional | no *(yes = assumes the milestone B gate passes, D104; re-validate after B-gate)* |
| Decisions | <Dxxx, Rxx> |
| Sources | [01-models.md §3.2](../../research/01-models.md), [19](../../research/19-review-resolutions.md) |
| Size | S (≤1 day) / M (2–3 days) / L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Why this task exists, with the measured problem or the decision it implements.

## Scope

**In:** …

**Out:** … (and which plan owns it)

## Checklist

- [ ] …
- [ ] Tests (100% coverage of new code)
- [ ] Changelog fragment / migration-registry entry when user-visible

## Acceptance criteria

- Observable, checkable statements. Benchmarks name the pinned input and the threshold.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|

## Validation

Commands a session runs before calling the task done.

## Workflow notes

Inputs consumed from other plans, outputs other plans rely on, what can run in parallel.

## Notes

Open problems found during implementation (empty at start).
