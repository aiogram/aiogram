# I-01 — Packaging hardening of the single `aiogram` distribution

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [B-01](../B-spike/B-01-crate-maturin-skeleton.md) |
| Blocks | [I-02](I-02-tier1-wheel-matrix-release.md), [I-04](I-04-installed-wheel-typing-stubtest.md), [I-08](I-08-contributor-workflow.md), [I-21](I-21-fresh-machine-install-rehearsal.md), [J-05](../J-ga/J-05-release-ownership-runbook-rollback.md) |
| Gate-conditional | no |
| Decisions | D1, D17, D119, R25, PD-27 |
| Sources | [08-build-release.md §2–4](../../research/08-build-release.md), [19 D119, R25](../../research/19-review-resolutions.md), [codex-review R25](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

B-01 ([B-spike](../B-spike/)) gives `dev-4.x` a minimal maturin build: `build-backend = "maturin"`,
`module-name = "aiogram._core"`, one crate and one CI job. That is enough to run the spike. It is not enough to publish.
The 3.x release pipeline (`.github/workflows/pypi-release.yml`: `uv build`, `twine check --strict`, a smoke install of
both wheel and sdist) assumes hatchling. 4.0 ships one distribution with the Rust core inside (D17) and no pure-Python
fallback (D1), so the following must be specified and tested:
- what goes into the wheel and the sdist;
- where the version comes from;
- what users see when no wheel matches.

R25 asks for exactly these tests: an offline sdist build, packaged stubs and data, installed wheels.

## Scope

**In:**
- `[tool.maturin]` include/exclude so the wheel ships `aiogram/**/*.py`, every generated `*.pyi`,
  `aiogram/_core/*.pyi`, `py.typed`, `aiogram/_migration/registry.toml` (PD-13) and the compiled `_core`. Tests,
  `crates/**/target`, `v4/`, `docs/_build` and `.butcher` state stay out.
- Sdist contents: `Cargo.toml`, `Cargo.lock`, `crates/**`, `rust-toolchain.toml`, Python sources and stubs. A CI job
  builds the sdist **offline** (`cargo vendor` or `--offline` with a pre-fetched registry) and installs it.
- A single version source and a CI equality check (decide item below). Port `scripts/bump_versions.py` and the
  Makefile `bump` / `update-api` targets to it.
- A clear failure when the extension is missing: `aiogram/__init__.py` wraps the `_core` import failure in an
  `ImportError` that names the interpreter tag and links the Install docs.
- `Development Status` classifier and pre-release handling for `4.0.0aN` / `bN` (alpha and beta are not GA, D121).

**Out:**
- The wheel matrix and publishing (I-02).
- Free-threaded jobs (I-03).
- Typing checks (I-04).
- PR CI layout (I-05).
- Dependency list changes (I-07).
- Contributor docs (I-08).

## Checklist

- [ ] Inventory what B-01 left in `pyproject.toml` / `Cargo.toml`. Drop the hatchling remnants (`[tool.hatch.*]`).
- [ ] `[tool.maturin]` `include` / `exclude`. Add `tests/test_packaging/test_wheel_contents.py`, which unpacks the built
      wheel and asserts the presence of `py.typed`, a sample of generated `.pyi` (e.g. `aiogram/types/message.pyi`),
      `aiogram/_core/*.pyi` and `registry.toml`, and the absence of `tests/`.
- [ ] Sdist manifest test: unpack it, assert the presence of `Cargo.lock` and `crates/`, and that no `target/` was packed.
- [ ] CI job `sdist-offline`: build the sdist, then `pip install --no-index` with a vendored cargo registry and
      network disabled for cargo (`CARGO_NET_OFFLINE=true`). Then `python -P -c "import aiogram"`.
- [ ] **Decide the version source of truth** (proposed default: `aiogram/__meta__.py` stays canonical for
      `__version__` / `__api_version__`. `scripts/bump_versions.py` also writes `[package] version` in
      `crates/aiogram-core/Cargo.toml`. pyproject keeps `dynamic = ["version"]` read by maturin from Cargo.toml. A test
      asserts `aiogram.__version__ == importlib.metadata.version("aiogram") == aiogram._core.__build_version__`).
      Record the choice in Notes and flag it to the owner.
- [ ] **Decide the unsupported-platform message** (proposed default: no custom build hook. maturin's own "Rust
      toolchain not found" stays the sdist failure. The Install docs (I-10) and README carry a "No wheel for your
      platform" box: Tier 1 / best-effort list, how to install Rust ≥ MSRV, Termux note. The `_core` import wrapper
      prints the wheel tag it expected). Record it in Notes and flag it to the owner.
- [ ] **Decide the MSRV promise** (proposed default: document "the Rust version pinned in `rust-toolchain.toml`
      or newer" as the sdist requirement. Do **not** promise "latest stable − 2" (08 §3) until I-02 has measured it.
      CI pins the toolchain separately from the documented MSRV, as R25 asks). Record it in Notes and flag it to the owner.
- [ ] Port the release smoke step (install wheel and sdist into a venv under `RUNNER_TEMP`, compare the
      `python -P` version) to the maturin build. I-02 reuses it.
- [ ] Classifiers: `Development Status :: 3 - Alpha` / `4 - Beta` during pre-releases, `5 - Production/Stable` at J-07.
- [ ] Tests (100% coverage of new Python code: the import-error wrapper and version helpers).
- [ ] Changelog fragment `CHANGES/<id>.misc.rst` ("aiogram is now built with maturin and contains a compiled core;
      installing from sdist needs Rust", README breaking change 7). Add the migration-registry entry for breaking change 7
      (kind `removal-4.0`, class manual, area "packaging & Python support") if A-11 hasn't seeded it.

## Acceptance criteria

- `maturin build --release` produces one wheel. The test suite above passes against it on Linux and macOS.
- `pip install aiogram-<v>.tar.gz` succeeds with cargo network disabled, given a pre-vendored registry.
- One command (`make bump` or the ported script) changes the version everywhere. The equality test fails if any
  copy drifts.
- With `_core` deleted from an installed wheel, `import aiogram` raises `ImportError` whose message names the
  interpreter tag and the Install docs URL (tested).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Separate `aiogram-core` distribution, exact-pinned | Bot API bumps change Rust and Python in lockstep; a split adds a pin, two pipelines and a mismatch failure mode | D17 |
| Pure-Python fallback when no wheel matches | Mandatory Rust core, pydantic way | D1 |
| abi3 wheels for 4.0 | abi3 can't load on free-threaded builds; per-version kept, CI cost accepted | 13 B16 declined, 08 §4 |
| cibuildwheel as the default builder | maturin-action is the starting point; cibuildwheel only if its test-in-wheel matrix is needed | 08 §4 |

## Validation

```bash
cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test
make dev                          # maturin develop
uv run pytest tests/test_packaging -q
maturin build --release && maturin sdist
uv run pytest tests
uv run mypy aiogram
```

## Workflow notes

- Input: B-01's skeleton.
- Outputs: the wheel layout (I-02, I-04, I-21), the version source (I-02, J-05, J-07) and the MSRV text (I-08, I-10).
- Can run in parallel with I-05 and I-12.

## Notes

(empty)
