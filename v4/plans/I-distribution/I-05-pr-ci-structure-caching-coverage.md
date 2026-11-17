# I-05 — PR CI structure, caching and coverage

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [B-01](../B-spike/B-01-crate-maturin-skeleton.md) |
| Blocks | [I-02](I-02-tier1-wheel-matrix-release.md), [I-06](I-06-largest-codegen-unit-guard.md), [I-07](I-07-dependencies-extras-restructure.md), [I-08](I-08-contributor-workflow.md), [C-23](../C-butcher/C-23-check-offline-determinism.md) |
| Gate-conditional | no |
| Decisions | D1, D7, D119, 13 B11, 13 B12, R25, R26 |
| Sources | [08-build-release.md §5](../../research/08-build-release.md), [13-aiogram-rust-review.md B11–B12](../../research/13-aiogram-rust-review.md), [19 R25](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

3.x CI (`.github/workflows/tests.yml`) runs pure Python:
- lint;
- a 3 OS × {3.11–3.15, pypy3.11} test matrix with Redis/Mongo on Linux and codecov uploads;
- a lowest-direct-deps job.

B-01 adds one Rust build job. On `dev-4.x` every test job needs a compiled extension (about 10 minutes for a release
build, 08 §3). Rebuilding that per matrix leg on every PR is expensive, and the decision table doesn't settle the
PR-time matrix: 08 §5 lists the full matrix, including PyPy, while D119 makes PyPy best-effort.

## Scope

**In:**
- Restructure `tests.yml` on `dev-4.x`: a **build-once** job produces wheels per interpreter and the test legs install
  them.
- Path filters: Python-only PRs reuse a wheel cached by the hash of `Cargo.lock`, `crates/**` and generated sources.
- rust-cache with `PYO3_ENVIRONMENT_SIGNATURE` in the key, `CARGO_INCREMENTAL=0`, debuginfo off (13 B12).
- Rust gates:
  - `cargo fmt --check`;
  - `cargo clippy --all-targets -D warnings`, with restriction lints `unwrap_used`, `expect_used`, `panic`, `todo`,
    `unimplemented` denied, also in generated code, and `allow(clippy::all)` must not mask them (13 B11);
  - `cargo test`.
- Coverage:
  - Python stays at 100% (the codecov upload logic stays);
  - Rust through `cargo-llvm-cov` over `cargo test` plus an instrumented pytest run;
  - generated code excluded from the Rust threshold only (R26: still executed by property/differential tests).
- A documented slot in the workflow structure where later plans add jobs; C-23 adds the `butcher-check` job itself
  (no placeholder job here).
- Required vs non-required jobs: PyPy legs are `continue-on-error` (D7, D119).

**Out:**
- Release matrix (I-02).
- ft jobs (I-03).
- Largest-unit guard (I-06).
- Benchmark regression job: A-05 / B-02 own the harness. This plan only reserves a non-required `bench` job slot.
- Lowest/newest dependency jobs (I-07).

## Checklist

- [ ] `build-wheels` job (Linux x86_64 per interpreter in the PR set) with the cache. Upload artifacts.
- [ ] `tests` legs: `uv sync --no-install-project` + install the artifact. Keep the 3.x Redis/Mongo service steps
      and the codecov logic.
- [ ] `rust` job: fmt, clippy (with a `clippy.toml` / `[lints]` table in `Cargo.toml`), test, llvm-cov.
- [ ] Path filter (`dorny/paths-filter` or native `paths`) choosing between "rebuild" and "reuse cached wheel".
      The cache key covers `Cargo.lock`, `crates/**`, `rust-toolchain.toml` and the `PYO3_ENVIRONMENT_SIGNATURE` value.
- [ ] **Decide the PR vs nightly matrix** (proposed default). Record the measured PR wall-clock in Notes and flag it to
      the owner.
      - **PR, required:** Linux cp311, cp314 and cp314t, full suite plus Redis/Mongo; macOS arm64 cp314; Windows x64 cp314.
      - **PR, non-required:** Linux pp311.
      - **Nightly (scheduled) and on push to `dev-4.x`:** the full 08 §5 matrix (3.11–3.15, 3.14t/3.15t,
        pp311/pp312, all three OSes).
- [ ] **Decide the stale "Python fallback encoder" wording** in 08 §5 ("request encoding, Rust vs the Python fallback
      encoder"). It contradicts D1, which allows no pure-Python fallback. Proposed default: there is no in-tree Python
      encoder. The request differential compares the Rust encoder against the external pinned 3.x oracle (A-09, PD-12),
      and D-15 owns those cases. Record it in Notes and flag it to A-02 for the research page fix.
- [ ] `make lint` on `dev-4.x` also runs `cargo fmt --check` and clippy, so local equals CI (AGENTS.md rule).
- [ ] Tests: the CI change is verified by a green run plus a forced-failure run (a clippy `unwrap()` in a scratch commit
      must fail).
- [ ] No changelog fragment (CI only, `skip news`).

## Acceptance criteria

- A Python-only PR (touching `aiogram/dispatcher/**` only) doesn't compile Rust: the job log shows a cache hit.
- A PR touching `crates/**` rebuilds, and the required set finishes; the wall-clock is recorded in Notes.
- `unwrap()` added to generated or hand-written Rust fails clippy.
- Python coverage stays at 100% (codecov gate). The Rust coverage report is published.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Full matrix on every PR | Cost about 10 min/leg × 20+ legs; nightly catches the rest | proposed default above |
| PyPy as a required check | Best-effort tier | D7, D119 |
| Excluding generated Rust from execution | Only from the % threshold; still executed | R26 |
| Python fallback encoder for differential tests | No pure-Python fallback | D1, PD-12 |

## Validation

```bash
cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test
make dev && uv run pytest tests
uv run mypy aiogram
make lint && make lint-workflows
```

## Workflow notes

- Input: B-01's minimal CI.
- Outputs:
  - cache keys and the wheel artifact convention (I-02, I-06, I-07);
  - the `make lint` contract (I-08).
- Run early, as soon as B-01 is done (PD-31 pulls B-01 ahead).

## Notes

(empty)
