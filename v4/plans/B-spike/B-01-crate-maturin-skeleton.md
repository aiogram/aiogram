# B-01 — Crate + maturin skeleton + minimal CI

| Field | Value |
|---|---|
| Status | `done` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md) |
| Blocks | [B-02](B-02-bench-adapter-memory-estimator.md), [B-03](B-03-decode-runtime.md), [B-09](B-09-sendmessage-encoder-response.md), [B-10](B-10-ext-helpers-stub-workflow.md), [B-11](B-11-cache-gc-teardown-ft-tests.md), [C-01](../C-butcher/C-01-crate-xtask-ir-snapshot.md), [D-07](../D-client/D-07-rust-encoder-json.md), [I-01](../I-distribution/I-01-packaging-hardening.md), [I-05](../I-distribution/I-05-pr-ci-structure-caching-coverage.md), [B-13](B-13-gate-run-and-decision.md), [D-08](../D-client/D-08-rust-encoder-multipart.md), [D-09](../D-client/D-09-response-decoder.md), [D-10](../D-client/D-10-request-snapshot-and-render-hook.md), [D-13](../D-client/D-13-raw-bot-call-raw-method.md), [D-17](../D-client/D-17-rust-entity-rendering-kernel.md), [G-15](../G-features/G-15-cli-core.md), [I-12](../I-distribution/I-12-deprecation-machinery-registry-ci.md) |
| Gate-conditional | no |
| Decisions | D1, D8, D17, D102, D119, PD-03, PD-31, R25 |
| Sources | [08-build-release.md §2, §3, §5, §6, §7](../../research/08-build-release.md), [07-free-threading.md §2, §5](../../research/07-free-threading.md), [13-aiogram-rust-review.md B4, B6, B11, B12](../../research/13-aiogram-rust-review.md), [19 R25](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Every Rust task in B, C, D and I needs a crate that builds and imports as `aiogram._core` inside the single `aiogram`
distribution (D1, D17). PD-31 pulls this skeleton ahead of its milestone. It also has to prove the toolchain choices
that the spike numbers depend on: pyo3 ≥0.30 (13 B6), the thin-LTO release profile (B4) and free-threading declared
from day one (D8).

## Scope

**In:**
- **Build backend.** `pyproject.toml` switches from `hatchling` to `maturin` (≥1.14). `[tool.maturin]` sets
  `python-source = "."`, `module-name = "aiogram._core"` and `manifest-path = "crates/aiogram-core/Cargo.toml"`.
  Includes keep shipping every `aiogram/**` Python file, `py.typed` and the locales, as the hatchling wheel does today.
- **Workspace.** A root `Cargo.toml` workspace with one crate, `crates/aiogram-core` (`cdylib`, D102). C-01 adds
  `crates/butcher` + `xtask` later.
- **Pins.** `pyo3` ≥0.30 and `jiter` pinned. `rust-toolchain.toml` (latest stable − 2 minors). Release profile:
  `opt-level = 3`, `lto = "thin"`, `codegen-units = 16`, `strip = true`.
- **Lints.** `[workspace.lints.clippy]` sets `unwrap_used`, `expect_used`, `panic`, `todo` and `unimplemented` to
  `deny` (B11).
- **Module.** `#[pymodule]` with free-threading support declared (never `gil_used = true`). It exposes only
  `__version__` and `build_info()` (pyo3 version, profile, target).
- **Stubs and build glue.** Hand-written stub `aiogram/_core.pyi`. `[tool.uv] cache-keys` cover `Cargo.toml`,
  `Cargo.lock` and `crates/**/*.rs` (08 §6). Makefile targets `dev` (`maturin develop`, debug) and `bench`
  (`maturin develop --release`).
- **Typing suite skeleton.** Create `tests/typing/` (an `__init__`-free directory of mypy-only test files with a
  `README` line on how it is run) and a Makefile target `typing` (`uv run mypy aiogram tests/typing`) using the repo's
  mypy config; later plans add cases there and I-04 runs it against the installed wheel.
- **Placement (PD-03).** `aiogram/types`, `aiogram/methods` and the rest of the 3.x package stay untouched. Nothing
  imports `_core` on the 3.x path.
- **CI (minimal).** A new workflow (e.g. `.github/workflows/core.yml`):
  - `cargo fmt --check`, `cargo clippy -D warnings`, `cargo test`;
  - `maturin develop` + the 3.x suite on Linux and macOS for cp311, cp313 and cp314t (`PYTHON_GIL=0`, fail if the
    GIL comes back);
  - a **Windows x64 build + import smoke** (Tier 1 per D119, and a cheap early check of `multiple-pymethods` /
    `inventory`, used in B-10);
  - rust-cache keyed with `PYO3_ENVIRONMENT_SIGNATURE`, incremental and debuginfo off (B12).
- **Conftest guard.** Added in `tests/conftest.py`: on a free-threaded build, fail the session if
  `sys._is_gil_enabled()` becomes true after `import aiogram._core`.

**Out:**
- Tier-1 wheel matrix and release workflow (I-02), free-threaded wheels (I-03), PyPy (unsupported in 4.x, PD-35).
- sdist hardening and packaging metadata polish (I-01).
- Largest-codegen-unit guard (I-06), coverage and caching structure (I-05), contributor docs (I-08).

## Checklist

- [x] Switch the build backend to maturin; check that `uv build` produces a wheel that contains the same Python files
  as the hatchling wheel (diff the file lists).
- [x] Decide the version source (proposed default: keep `aiogram/__meta__.py` as the source of truth that
  `make update-api` / the release skill bump. maturin reads a static `version` in `pyproject.toml`, which the bump
  script updates in the same commit; a test asserts both are equal). Record in Notes and flag to owner. I-01 hardens
  this.
- [x] Add the Cargo workspace, crate, `rust-toolchain.toml`, release profile and lint table.
- [x] Add a `#[pymodule]` with `__version__` and `build_info()`; update `aiogram/_core.pyi`.
- [x] Export the `_core` build metadata G-15's `aiogram info` reports: `build_info()` returns at least `version`,
  `profile` and `target` (plus the pyo3 version), typed in `aiogram/_core.pyi`.
- [x] Add `[tool.uv] cache-keys`, and the Makefile `dev` / `bench` / `typing` targets; create `tests/typing/`.
- [x] Add the CI workflow. `make lint-workflows` (zizmor) must pass.
- [x] Add the conftest free-threading guard.
- [x] Tests: `tests/test_core/test_build.py` checks import, `build_info()` fields, the version equality, and the
  GIL-disabled check on free-threaded builds (100% of new Python).
- [x] No changelog or registry entry (internal; the Rust toolchain requirement for sdist is breaking change 7, which
  I-01 owns).

## Acceptance criteria

- `uv sync` from a clean checkout builds the extension, and `python -c "import aiogram._core"` works on cp311,
  cp313 and cp314t.
- On cp314t, `sys._is_gil_enabled()` is `False` after the import, without `PYTHON_GIL=0`.
- `uv run pytest tests` (the unchanged 3.x suite) passes with the extension installed. `import aiogram` doesn't load
  `_core` (checked through `sys.modules`).
- `cargo clippy --workspace --all-targets -- -D warnings` passes with the restriction lints on.
- `make typing` runs mypy over `tests/typing/` (empty suite passes).
- The CI workflow is green on Linux and macOS (cp311, cp313, cp314t) and the Windows smoke.
- `build_info()` reports pyo3 ≥0.30 and, for `make bench`, profile `release` with thin LTO.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| A separate `aiogram-core` distribution | Exact pin, two pipelines, a version-mismatch failure mode | D17 |
| A three-crate layout (types / glue / bindings) | One crate with placement rules: −137 s build, −16% binary (aiogram_rust PR #11) | D102, 13 §7 |
| A pure-Python fallback | Mandatory core | D1 |
| abi3 wheels | Can't load on free-threaded builds; per-version kept | D119, 13 B16 |
| Fat LTO | Tripled build time, ran a 16 GB runner out of memory, ≈2% gain | 13 B4 |
| pyo3 <0.30 | Reference-pool mutex on every call once a `Py` is dropped while detached | 13 B6 |
| tokio / pyo3-async-runtimes | No async in Rust | 08 §3, 05 §3 |

## Validation

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
make dev
uv run pytest tests
uv run mypy aiogram
make lint
make lint-workflows
```

## Workflow notes

- Output for G-15: `build_info()` build metadata (version, profile, target) for `aiogram info`.
- Output for C-01, D-07, I-01 and I-05: the workspace layout, toolchain pins, the CI job and the `_core` module entry
  point.
- B-03, B-09, B-10 and B-11 add modules to this crate. Placement rules 08 §7 items 13–16 apply from the first type.
- Can run in parallel with B-00.

## Notes

- **Version source (Decide, proposed default taken; flag to owner).** `aiogram/__meta__.py` stays the source of
  truth. `scripts/bump_version.py` also writes the static `version` in `pyproject.toml` (read by maturin) and in
  `crates/aiogram-core/Cargo.toml` (`_core.__version__` is `CARGO_PKG_VERSION`); `make bump` then refreshes
  `Cargo.lock` and `uv.lock`, because a static project version is recorded in `uv.lock` and `uv sync --locked`
  fails on a mismatch. `tests/test_core/test_build.py` asserts all copies are equal. Only `X.Y.Z` versions are
  handled (as before); I-01 hardens this, including PEP 440 → semver for pre-releases.
- **`build_info()`** returns `version`, `pyo3_version`, `profile`, `lto` and `target`. `build.rs` reads the pyo3
  version from `Cargo.lock` and the `lto` value of the active profile from the workspace `Cargo.toml` (or a
  `CARGO_PROFILE_<P>_LTO` override); cargo does not expose LTO to build scripts, so this is the configured value.
- **sdist content changed.** maturin's sdist holds only the crate, the `aiogram/` package, `pyproject.toml`,
  `README.rst` and `LICENSE`; hatchling's also carried `tests/`, `docs/`, `.butcher/` and other repo files. The
  wheel file list is identical to the hatchling one plus `aiogram/_core.*.so`. Left to I-01 (sdist hardening).
- **CI.** `core.yml` builds with `maturin develop --uv --release` (08 §5) after a `--no-install-project` sync.
  The 3.14t leg runs with `PYTHON_GIL=0`: `hiredis` re-enables the GIL at import otherwise (07 §4). The existing
  `tests.yml` legs on `dev-4.x` now compile the extension through `uv sync` too (runners ship `rustup`).
- **Not done here:** Dependabot `cargo` ecosystem (I-05), a release workflow for platform wheels (I-02;
  `pypi-release.yml` only fires on `v3.*` tags).
