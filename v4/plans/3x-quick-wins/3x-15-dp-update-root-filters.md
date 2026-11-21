# 3x-15 — `dp.update.filter` root filters are actually checked (and the rest of the filter-correctness bundle)

| Field | Value |
|---|---|
| Status | `done` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | — (A-10 decoupled by the owner, 2026-11-18; see Notes) |
| Blocks | — |
| Gate-conditional | no |
| Decisions | PD-28 (behaviour change → 3.x minor); 03 §3 `root_filters` incl. `dp.update.filter` |
| Sources | [09 #17](../../research/09-3x-quick-wins.md), [03 §3](../../research/03-routing.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`Dispatcher.feed_update` passes `self.update.trigger` to `wrap_outer_middleware`, and
`TelegramEventObserver.trigger` never calls `check_root_filters`. So filters registered with `dp.update.filter(...)`
are **never evaluated**, and bot-wide guards are silently bypassed. This is a regression from #1267 and OSS Scanner
finding **ANT-2026-EZKREY5K** (09 #17).

**One PR for the related OSS Scanner findings** ("Filter correctness"). The findings and fix shapes as planned (the
Notes record what changed before shipping):

| Finding | Fix |
|---|---|
| ANT-2026-EZKREY5K | Make `dp.update` root filters run, for example a `Dispatcher._trigger_update` that calls `check_root_filters` before `trigger`. The scanner patch is correct |
| ANT-2026-RO3G83HJ | `_AndFilter` must `kwargs.update(result)` so dict results propagate through `and_f` (`aiogram/filters/logic.py`) |
| ANT-2026-664Y7GWN | Refresh `__all_states_names__` recursively for `StatesGroup` nested 3+ levels (`aiogram/fsm/state.py`); regression since #1507 |
| ANT-2026-IYO3AS6K | A filter whose sync callable returns a coroutine must not pass as a match (`aiogram/dispatcher/event/handler.py`). Shipped shape in Notes |
| ANT-2026-9QFTXU7P | Filters passed to `on.message.enter(...)` in Scenes are silently dropped: reject them or emit a `DeprecationWarning`, and document it. The scanner patch checks the wrong update type and is not usable |
| ANT-2026-0M5J1VQ7 | `CallbackData.pack()`: a post-join round-trip check, so a self-overlapping multi-character separator (`"--"`) can't shift characters into the next field |

## Scope

**In:** all six fixes above, one test file each (or one per touched module), plus docs for 9QFTXU7P.

**Out:**
- Routing performance: 3x-03 / 3x-11.

## Checklist

- [ ] EZKREY5K: root filters on `dp.update` run, and a failing one makes the update `UNHANDLED`, with outer
      middlewares still running as today. Test both polling and webhook paths.
- [ ] RO3G83HJ, 664Y7GWN, IYO3AS6K, 9QFTXU7P, 0M5J1VQ7, as specified in the table.
- [ ] Decide 9QFTXU7P: raise `TypeError` or warn (`DeprecationWarning`) for filters passed to `.enter()`. Proposed
      default: warn in 3.x, because raising would break bots that currently "work" with silently ignored filters.
      Record the choice in Notes and flag it to the owner.
- [ ] A-10 routing oracle, parent vs this commit:
  - the root-filter cases change; record them as an approved 3.x difference (decision `ANT-2026-EZKREY5K`);
  - everything else stays invariant except the fixed bugs, which are listed one by one.
- [ ] 100% coverage.
- [ ] Changelog: one fragment per finding (`CHANGES/<pr>.bugfix.rst`, or several with a distinct issue id each):
  - each ends "Reported by the Anthropic OSS Scanner (ANT-2026-…).";
  - EZKREY5K's fragment warns that existing `dp.update.filter(...)` registrations **start being enforced**.
- [ ] One `Reported-by: Anthropic OSS Scanner (ANT-2026-…)` commit trailer per finding.
- [ ] Ship in a 3.x **minor**, not a patch (PD-28).
- [ ] Migration registry: no entry. 03 §3 already folds root filters into the 4.0 snapshot.

## Acceptance criteria

- `dp.update.filter(lambda u: False)` makes every update `UNHANDLED`, and no handler runs.
- Each listed finding has a regression test that fails on the parent commit and passes here.
- The A-10 oracle shows only the listed, approved differences.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Ship as a patch release | The root filters starting to enforce is a visible behaviour change | PD-28 |
| Scanner patch for 9QFTXU7P as-is | Checks the wrong update type | — |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m differential run --kind routing --left git:HEAD~1 --right git:HEAD
```

## Workflow notes

- E-02 compiles `root_filters` per router, including `dp.update`. This plan is its 3.x precedent.
- 3x-12 (`State.state` caching) should land after 664Y7GWN or be rebased onto it.

## Notes

- Owner, 2026-11-18: decoupled from A-10 so the fix (and the PD-34 embargo) is not held behind the routing oracle.
  Ship with ordinary unit tests; the A-10 checklist item and the "A-10 shows only the listed differences" criterion
  move to a follow-up run once A-10 is done (record the root-filter change there as an approved 3.x difference).
- Owner, 2026-11-18: publish through a **GHSA private fork** (advisory + 3.x minor together; ids only in the advisory
  credit, not in public commits, trailers or changelog fragments). 9QFTXU7P: `DeprecationWarning` (default accepted).
- Owner, later on 2026-11-18: the fix **does** credit the scanner as the checklist says (changelog "Reported by the
  Anthropic OSS Scanner (ANT-…).", a `Reported-by` trailer per finding, credits in the PR body); the bugs are not
  critical enough to hide the credit. Repro code and write-up text still stay out.
- Owner review, 2026-11-18: one more planned row (`.as_()` treating a `False` value as a match) is **not a bug**;
  the 3.x behaviour stays and is documented; dropped from the fix, the changelog and the advisory.
- Owner, 2026-11-18: IYO3AS6K reworked — a filter whose sync callable returns a coroutine (later: any awaitable)
  raises `TypeError` (fail closed); nothing is awaited, a coroutine is closed. The planned `partial`/`@wraps`
  classification change was dropped (dev-3.x behaviour).
- Shipped in aiogram 3.33.0; advisory: https://github.com/aiogram/aiogram/security/advisories/GHSA-fvpw-9jw8-rj3h.
