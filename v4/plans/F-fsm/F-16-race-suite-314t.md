# F-16 — FSM race and concurrency suite on 3.14t (F exit gate)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-01](F-01-thread-safe-memory-storage.md), [F-02](F-02-isolation-lock-table-default-on.md), [F-03](F-03-release-isolation-warn-after.md), [F-06](F-06-redis-storage-legacy-layout.md), [F-13](F-13-scenes-d33.md), [F-15](F-15-statefilter-state-index.md), [I-03](../I-distribution/I-03-free-threaded-wheels-ci.md), [E-22](../E-runtime/E-22-single-bot-sharding.md) |
| Blocks | [F-17](F-17-fsm-docs-migration-page.md), [J-01](../J-ga/J-01-feature-inventory-audit.md), [H-20](../H-testing-observability/H-20-integration-layer-exit-gate.md), [I-20](../I-distribution/I-20-examples-port-smoke.md), [I-23](../I-distribution/I-23-beta-pre-release.md) |
| Gate-conditional | no |
| Decisions | D8, D28, D110, R14, PD-04, PD-26 |
| Sources | [04-fsm.md §2, §4 note, §9](../../research/04-fsm.md), [07-free-threading.md §5](../../research/07-free-threading.md), [codex-review.md R14](../../research/codex-review.md), [README milestone F](../../research/README.md), [plans README §1](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Milestone F's exit gate is "race tests on 3.14t; application lost-update limits documented". The bugs in 04 §2 were
found with the GIL on and get worse without it. R14's acceptance asks for adversarial cancellation around every
hand-off, closed-loop waiters, pruning/recreation under contention, explicit nested-data behaviour, and **separate**
tests for atomic merge versus serialised read-modify-write (an atomic merge alone does not prevent lost updates).

## Scope

**In:**
- `tests/test_fsm/test_races.py` (marker `race`), run on the normal build with `sys.setswitchinterval(1e-6)` and on
  3.14t / 3.15t with `PYTHON_GIL=0` in the I-03 CI jobs:
  1. lock-table duplicate-lock race (3.x: 13/3000) across 8 threads;
  2. one isolation shared by 2–4 loops in threads (3.x: 400/800 `RuntimeError`);
  3. MemoryStorage atomic merge: distinct keys merged concurrently, none lost;
  4. **serialised read-modify-write**: 4 threads × N increments of one counter under isolation end at exactly 4N;
     the same **without** isolation is documented as lossy (the test asserts the docs' claim, not a fix);
  5. scene history aliasing under concurrent transitions of different keys;
  6. adversarial cancellation at each hand-off state (queued, granted-not-resumed, acquired), closed waiter loop,
     pruning and re-creation under contention;
  7. `release_isolation` under contention: ask-and-wait across threads; re-entrant same-task acquisition raises
     (PD-26); release hooks (PD-04) run before the next waiter is granted;
  8. nested-value aliasing behaviour asserted exactly as F-01 decided;
  9. **cross-loop lock table under E-22 single-bot sharding:** one ingress feeding 4 worker Runners (each its own loop
     and thread) over a shared F-02 isolation; updates for the same key arriving on different workers serialise, no
     worker loop blocks on a lock held by another loop, and nothing deadlocks (bounded by the per-test timeout),
     including cancellation of a waiter while the holder runs on another loop.
- Redis variants of 4 and 7 under `--redis` (in-process isolation and `RedisEventIsolation`).
- conftest check: on free-threaded builds, fail the session if `sys._is_gil_enabled()` becomes true after import
  (07 §5) — coordinate with I-03 if it already adds this.
- Docs: the lost-update limits page section (F-17 links it): what `update_data` guarantees per storage, what needs
  isolation, multi-process Redis needs `RedisEventIsolation`.

**Out:**
- The 3.14t CI job itself: I-03.
- Rust-core thread tests (decode, views): B-11.

## Checklist

- [ ] Race tests 1–9 (9 on E-22's sharding harness) and the Redis variants; register the `race` marker in the pytest config in `pyproject.toml`.
- [ ] GIL re-enable guard in `tests/conftest.py` (or confirm I-03's).
- [ ] Each test bounded by a timeout (no hung CI); seeds and iteration counts as constants at the top of the file.
- [ ] Lost-update limits docs section.
- [ ] Tests (100% coverage of new code)
- [ ] Changelog fragment in `CHANGES/` (docs).

## Acceptance criteria

- All race tests pass 20 consecutive runs on CPython 3.13 (switch interval 1e-6) and on 3.14t with `PYTHON_GIL=0`
  in CI (I-03 job), each run under 120 s.
- The serialised read-modify-write test ends at exactly 4N with isolation.
- The sharded cross-loop test (9) completes every update exactly once with per-key order preserved and no deadlock in
  all 20 runs on 3.14t.
- Lost-update limits are documented and linked from the FSM docs.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Use an increment stress test as proof that `update_data` is safe | Atomic merge ≠ atomic application RMW | R14 |
| Run race tests only on GIL builds | Free-threading is first-class on 3.14t+ | D8 |

## Validation

```bash
make dev
uv run pytest tests/test_fsm -m race -q
uv run pytest --redis redis://localhost:6379/0 tests/test_fsm -m race -q
PYTHON_GIL=0 uv run --python 3.14t pytest tests/test_fsm -m race -q
uv run pytest tests
make lint
```

## Workflow notes

- F exit gate. J-01 (feature inventory audit) reads its result.
- Reuses E-22's sharding harness for test 9; E-22 relies on this plan for the cross-loop no-deadlock coverage.

## Notes
