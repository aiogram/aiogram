# 3x-14 — `CallbackData`: prefix fast-fail before split and validate

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-05](../A-contracts/A-05-bench-harness.md) |
| Blocks | [A-06](../A-contracts/A-06-record-3x-baselines.md) |
| Gate-conditional | no |
| Decisions | — (11 §4 notes the fast-fail also serves 4.0's non-pydantic `CallbackData`) |
| Sources | [09 #16](../../research/09-3x-quick-wins.md), [11 §4 CallbackData](../../research/11-removals.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`CallbackQueryFilter.__call__` (`aiogram/filters/callback_data.py`) always calls `CallbackData.unpack(query.data)`,
which splits the string and validates it with pydantic, and only then finds out that the prefix differs. A
non-matching filter costs ≈8 µs, against 0.2 µs with a prefix check. A bot with many `CallbackData` classes pays
that on every callback for every non-matching filter.

## Scope

**In:**
- In `CallbackQueryFilter.__call__`, return `False` when
  `query.data != prefix and not query.data.startswith(prefix + separator)`, before calling `unpack`.
- The result must equal what the `unpack` error path produces today. Check the edge cases: a prefix with no fields,
  an empty string, and a separator inside the prefix (forbidden by `CallbackData` class creation; confirm it).

**Out:** the 4.0 `CallbackData` rewrite: F-11.

## Checklist

- [ ] Baseline with A-05 on `callback_data.filter.miss` (20 non-matching classes, one matching).
- [ ] Add the fast-fail.
- [ ] Tests:
  - parametrised equivalence against `unpack` over prefixes, separators, field counts and empty data;
  - the matching path is unchanged.
- [ ] Coordinate with [3x-15](3x-15-dp-update-root-filters.md): its `CallbackData` change touches `pack()`, not the filter, so there is
      no conflict; confirm it.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.misc.rst`.
- [ ] Migration registry: no entry.

## Acceptance criteria

- A-05 `compare` on `callback_data.filter.miss`: median ≥ 10× faster than the parent commit.
- The equivalence test shows identical results for every generated input.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Rust `CallbackData` | Pack/unpack cost is the user's field conversion; the fast-fail covers most of it | 11 §4 |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases callback_data.filter.miss
```

## Workflow notes

F-11 must keep the fast-fail in the non-pydantic implementation.

## Notes
