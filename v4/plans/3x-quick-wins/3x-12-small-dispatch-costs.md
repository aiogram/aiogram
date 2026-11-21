# 3x-12 — Small per-update dispatch costs

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-05](../A-contracts/A-05-bench-harness.md), [3x-11](3x-11-prebuilt-middleware-chains.md) (rebase order) |
| Blocks | [A-06](../A-contracts/A-06-record-3x-baselines.md) |
| Gate-conditional | no |
| Decisions | — (09 #12 non-lock part, #13) |
| Sources | [09 #12, #13](../../research/09-3x-quick-wins.md), [04 §1](../../research/04-fsm.md), [03 §2](../../research/03-routing.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

A handful of µs per update are spent on avoidable work:
- `DisabledEventIsolation.lock` is a generator-based `@asynccontextmanager` (≈1.1 µs);
- `FSMContextMiddleware` reads `bot.id` per update, which parses the token;
- `StateFilter.__call__` scans a sequence for every check;
- `State.state` is recomputed on every access.

## Scope

**In:**
- `DisabledEventIsolation.lock` (`aiogram/fsm/storage/memory.py`) returns a shared `contextlib.nullcontext()`,
  which supports `async with`.
- Cache the bot id on the `Bot` instance (`aiogram/client/bot.py`): compute it once from the token, which is
  immutable. Check how `Bot.id` is implemented today, and whether `utils/token.py` already has an `lru_cache`; keep
  the public behaviour.
- `StateFilter` (`aiogram/filters/state.py`): precompute a `frozenset` of plain string states (including `"*"` and
  `None`) at construction, so the str/None check is O(1). Keep the order and semantics for `State`, `StatesGroup`
  and class entries.
- `State.state` (`aiogram/fsm/state.py`): compute it once when the group is set, invalidated if the state is
  re-attached to a group.

**Out:** the `SimpleEventIsolation` lock: [3x-06](3x-06-isolation-lock-pruning.md). 09 #12's "return the
`asyncio.Lock`" is rejected there.

## Checklist

- [ ] Baseline with A-05 on `routing.1-handler`, in its FSM-on variant.
- [ ] Make the four changes. Each must keep its public return types; `DisabledEventIsolation.lock()` must still work
      with `async with`.
- [ ] Tests:
  - `State.state` is correct after `StatesGroup` subclassing and nesting, including 3+ level groups;
  - `StateFilter` matches the same inputs as before (parametrised over the existing cases);
  - the bot id is unchanged.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.misc.rst`.
- [ ] Migration registry: no entry.

## Acceptance criteria

- A-05 `compare` on `routing.1-handler` (FSM on): median ≥ 1 µs faster than the parent commit.
- Every existing FSM and filter test passes unchanged.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Bare `asyncio.Lock` from `SimpleEventIsolation.lock` | Bypasses pruning bookkeeping | R27 (3x-06) |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases routing.1-handler
```

## Workflow notes

- If `State.state` caching interacts with [3x-15](3x-15-dp-update-root-filters.md), land 3x-15 first and record it.
- F-04 reworks the 4.0 FSM hot paths.

## Notes
