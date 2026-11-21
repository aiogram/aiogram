# B-11 — Cache / GC / teardown / free-threading tests

| Field | Value |
|---|---|
| Status | `todo` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-05](B-05-views-cache-gc-routing-keys.md), [B-06](B-06-value-semantics-native-api.md), [B-07](B-07-bound-views.md), [B-08](B-08-subclassing-register.md), [B-09](B-09-sendmessage-encoder-response.md), [B-01](B-01-crate-maturin-skeleton.md) |
| Blocks | [B-13](B-13-gate-run-and-decision.md) |
| Gate-conditional | no |
| Decisions | R03, D8, D103, D87 (depth), PD-03 |
| Sources | [01-models.md §3.1, §4, §5 item 5](../../research/01-models.md), [07-free-threading.md §2, §5](../../research/07-free-threading.md), [codex-review.md R03](../../research/codex-review.md), [19 R03](../../research/19-review-resolutions.md), [13-aiogram-rust-review.md B6, B7](../../research/13-aiogram-rust-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

"Cache/GC/teardown tests pass" is part of the binding gate (README B row). R03's acceptance list is concrete:
- concurrent first access returns one wrapper;
- callback re-entry can't deadlock;
- cycles through Bot / session / user state are collectable;
- teardown works on the lowest supported CPython and on free-threaded builds.

This task turns those into the named test ids B-00 lists.

## Scope

**In** (a `tests/test_core/test_lifetime_*.py` suite plus a few `cargo test` cases):
- **Concurrent first access.** N=32 threads on cp314t (`PYTHON_GIL=0`) call `update.message.chat` on one view
  through a barrier. All receive the identical object; the losers' allocations are freed (B-02 `_alloc_stats()`
  returns to baseline).
- **Re-entry.** A registered subclass (B-08) whose property accessed during materialisation reads the same parent's
  cache. A lazy-text render hook (B-09) that decodes and encodes inside the callback. Both finish (no deadlock, a
  10 s timeout fails the test) on cp311 and cp314t.
- **Cycles.**
  - A `Bot`-like Python object holding a bound update that holds the bot; a user subclass instance that stores the
    message in its own attribute; a session object referencing a cached child.
  - After `del` + `gc.collect()`, weakrefs to the Python participants are dead and `_alloc_stats()` live bytes return
    to baseline.
- **Teardown.** A subprocess that leaves bound views, cycles and registered subclasses alive at interpreter exit.
  Exit code 0, no fatal error, on cp311 and cp314t.
- **07 §5 races.**
  - Concurrent decode of the same raw bytes from N threads.
  - Contended `as_()` views of one payload for different bots: neither redirects the other (B-07 extends this).
  - Concurrent `.raw` / `to_dict()` on one object.
- **Depth.** 129 levels → decode error; a 10 000-level iterative-drop test on cp311.
- **GIL.** The conftest guard (B-01) is active, so the whole suite fails if the GIL is re-enabled.
- **Optional.** A scheduled nightly ThreadSanitizer job (`RUSTFLAGS=-Zsanitizer=thread`), non-blocking.

**Out:**
- FSM / isolation race suites (F-16).
- Runner / multi-loop tests (E-19).
- Benchmark numbers (B-02 / B-13).

## Checklist

- [ ] Concurrent first-access test with a barrier and an allocation check.
- [ ] Re-entry tests (subclass property, render hook) with timeouts.
- [ ] Cycle-collectability tests with weakrefs and an allocation check.
- [ ] Interpreter-teardown subprocess tests on cp311 and cp314t.
- [ ] 07 §5 race tests.
- [ ] Depth and iterative-drop tests.
- [ ] Add the cp314t run of `tests/test_core` to the B-01 CI workflow with `PYTHON_GIL=0`.
- [ ] Decide whether the TSan job is added now (proposed default: yes, scheduled weekly, non-blocking, owned by I-03
  afterwards). Record in Notes and flag to owner.
- [ ] Give each test the id B-00's `gate.toml` names, so B-13 can map results to gate items.
- [ ] No changelog or registry entry (tests only).

## Acceptance criteria

- Every gate-named lifetime test passes on Linux and macOS for cp311 and cp314t, and in CI.
- The concurrent first-access test passes 100 repeated runs on cp314t without a mismatch.
- No test needs a sleep-based wait; each blocking test fails within its timeout instead of hanging CI.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Relying on `OnceLock` as proof of safety | Initialisation can run Python; re-entrancy is a separate hazard | R03 |
| Testing only on GIL builds | Free-threading is first-class on 3.14t+ | D8 |
| 3.13t | Out of scope; PyO3 0.29 dropped it | 07 |
| Supporting subinterpreters | PyO3 refuses import; unsupported | 19 R03 |

## Validation

```bash
cargo test --workspace
make dev
uv run pytest tests/test_core
PYTHON_GIL=0 uv run --python 3.14t pytest tests/test_core
uv run pytest tests
make lint
```

## Workflow notes

- Inputs: B-05..B-09 behaviour.
- Outputs: the gate's semantic results for B-13; patterns reused by F-16, E-19 and E-22 race suites.
- Tests can be written against B-05 early and extended as B-06..B-09 merge.

## Notes
