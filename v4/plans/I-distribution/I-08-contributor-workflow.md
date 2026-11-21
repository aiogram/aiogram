# I-08 — Contributor workflow for `dev-4.x`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-01](I-01-packaging-hardening.md), [I-05](I-05-pr-ci-structure-caching-coverage.md), [C-23](../C-butcher/C-23-check-offline-determinism.md) |
| Blocks | [I-10](I-10-diataxis-docs-skeleton.md) |
| Gate-conditional | no |
| Decisions | D6, D17, 08 §6 |
| Sources | [08-build-release.md §6–7](../../research/08-build-release.md), [02-butcher.md](../../research/02-butcher.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Today's contributor docs assume a pure-Python repo: `CONTRIBUTING.md`, `docs/contributing.rst`, AGENTS.md and CLAUDE.md
describe `uv sync`, `make lint`, `uv run pytest tests` and the Python butcher (`uv run --extra cli butcher parse/refresh/apply`).

On `dev-4.x`:
- `uv sync` builds a Rust extension;
- Bot API bumps go through `cargo xtask butcher` (D6);
- the generated Rust and Python must stay in lockstep.

08 §6 says most contributions stay pure Python, but every contributor still needs `rustup` to build.

## Scope

**In:**
- `CONTRIBUTING.md` and `docs/contributing.rst` (moved under "Contributing" in the I-10 tree): rustup, `uv sync`
  rebuilding through maturin (`[tool.uv] cache-keys` includes `Cargo.toml`, `Cargo.lock`, `crates/**/*.rs`), `make dev`
  (debug `maturin develop`), `make bench` (release).
- Butcher flow: `cargo xtask butcher` (fetch / emit / check / diff, per C plans), the PD-10 `import-legacy` shim.
- Debugging across the boundary: `py-spy record --native`, `perf` with `-X perf`. `PanicException` means a bug: report
  it (08 §6, §7.8).
- Rewrite AGENTS.md / CLAUDE.md on `dev-4.x` (base branch, checks, codegen rules for the Rust butcher). The 3.x copies
  stay on `dev-3.x`.
- Changelog / towncrier conventions on `dev-4.x` (unchanged categories).

**Out:**
- The skeleton Makefile targets themselves (B-01 / I-01).
- CI (I-05).

## Checklist

- [ ] Rewrite `CONTRIBUTING.md` sections: setup, quick loop (`make lint`, `uv run pytest tests`), the Rust loop
      (`cargo fmt`, `clippy`, `cargo test`, `make dev`), the butcher loop.
- [ ] Verify `[tool.uv] cache-keys` triggers a rebuild after touching a `.rs` file (manual check, recorded in Notes).
- [ ] **Decide prebuilt wheels for Python-only contributors** (proposed default: not in 4.0; rustup is a documented
      requirement. CI-built wheels from I-05 are downloadable as workflow artifacts for reviewers, and the docs say so.
      Revisit if contributor feedback during the beta (J-03) shows rustup is a barrier). Record it in Notes and flag it
      to the owner.
- [ ] AGENTS.md / CLAUDE.md for `dev-4.x`: base branch `dev-4.x`, commands, "never hand-edit `crates/aiogram-core/src/generated/**`".
- [ ] Docs-only contributors: mention that docs build without Rust (I-09).
- [ ] No tests needed beyond a docs build; no changelog fragment (`skip news`).

## Acceptance criteria

- A fresh clone on macOS and Linux following CONTRIBUTING.md reaches green `make lint` and `uv run pytest tests`. This
  is recorded once in Notes with timings.
- Every command in CONTRIBUTING.md and AGENTS.md exists, checked by `make -n <target>` / `cargo xtask --help`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keeping the Python butcher for 4.x | Retired; Rust butcher | D6 |
| A separate pure-Python dev mode without `_core` | No fallback | D1 |

## Validation

```bash
make dev && make lint && uv run pytest tests
cargo xtask butcher check
uv run --group docs bash -c 'cd docs && make html'
```

## Workflow notes

- Inputs: I-01 (Makefile/version), I-05 (`make lint` contract), C-23 (butcher commands).
- Output: Contributing page content for I-10.

## Notes

(empty)
