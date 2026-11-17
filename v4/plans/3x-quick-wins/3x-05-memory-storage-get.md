# 3x-05 — `MemoryStorage` reads stop creating records

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-05](../A-contracts/A-05-bench-harness.md) |
| Blocks | — |
| Gate-conditional | no |
| Decisions | — (pure bugfix; R27 lists it as "independently verified") |
| Sources | [09 #3](../../research/09-3x-quick-wins.md), [04 §1–2](../../research/04-fsm.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`MemoryStorage.storage` (`aiogram/fsm/storage/memory.py`) is a `defaultdict(MemoryStorageRecord)`. `get_state`,
`get_data` and `get_value` index it with `self.storage[key]`, so every read creates a record. That costs 537 B per
stateless user, and the growth is unbounded: every user who ever wrote to the bot keeps a record.

## Scope

**In:**
- The read paths `get_state`, `get_data` and `get_value` use `self.storage.get(key)`.
- On a missing key they return `None` for state, `{}` for data, and `default` for a value.
- Writes keep creating records.
- Data stays copied on read, as today.

**Out:**
- Pruning records after `clear()` / `set_state(None)` with empty data. That changes when records disappear; leave it
  to F-01 (4.0), or propose it here as a decision item if it turns out to be trivial.
- Lock-table pruning: [3x-06](3x-06-isolation-lock-pruning.md).

## Checklist

- [ ] Change the three read paths.
- [ ] Test: after 1 000 `get_state` / `get_data` / `get_value` calls for distinct keys, `len(storage.storage) == 0`.
- [ ] Test: the returned data is still a copy, so mutating it doesn't change storage.
- [ ] Optionally measure `fsm.memory.stateless-read` with A-05 for the record.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.bugfix.rst`.
- [ ] Migration registry: no entry.

## Acceptance criteria

- Reads never add keys to `MemoryStorage.storage`. Every existing `tests/test_fsm/storage` case passes.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Replace `MemoryStorage` with a thread-safe one now | 4.0 work (F-01, PD-21) | D27/D28 scope |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
```

## Workflow notes

Independent. Can ship together with 3x-06 in one release; they are separate PRs.

## Notes
