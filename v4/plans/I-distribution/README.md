# I — Distribution & migration beta

**Goal.** Make 4.0 installable everywhere Tier 1 promises, and documented without a Rust toolchain. Give 3.x users tools
that do most of the migration for them:
- packaging and the wheel matrix (D17, D119, PD-27);
- free-threaded wheels (D8);
- the dependency restructure (D67–D70);
- the import-free docs build and the Diátaxis docs (D79–D81, R29);
- the 4.x deprecation machinery on the shared registry (D71–D72, D82, PD-13);
- `aiogram migrate check/fix` (D74, R28, D100);
- the ported examples;
- the 4.0 beta.

**Exit gate (README D121).** Fresh-machine install (I-21) and 3→4 migration rehearsal (I-22) pass across Tier 1.

**Normative inputs.** [plans README §1](../README.md) (PD-01 to PD-31) → [19](../../research/19-review-resolutions.md)
→ research pages. Relevant PDs: PD-13 (registry data file), PD-27 (Tier 1 = our wheels and our suite), PD-31 (B-01 and
I-12 pulled early).

**Not here:**
- the build skeleton is **B-01** ([B-spike](../B-spike/)); I-01 builds on it;
- the 3.x migration-baseline warnings are **3x-20 to 3x-24** ([3x-quick-wins](../3x-quick-wins/)). I-13 was merged
  there and has no file;
- the registry schema, ids and seed are **A-11** ([A-contracts](../A-contracts/)).

## Tasks

| ID | Title | Depends on | Gate-cond. | Size |
|---|---|---|---|---|
| [I-01](I-01-packaging-hardening.md) | Packaging hardening of the single distribution | B-01 | no | M |
| [I-02](I-02-tier1-wheel-matrix-release.md) | Tier-1 wheel matrix + release workflow | C-02, C-18, I-01, I-05 | no | L |
| [I-03](I-03-free-threaded-wheels-ci.md) | Free-threaded wheels + CI | I-02 | no | M |
| [I-04](I-04-installed-wheel-typing-stubtest.md) | Installed-wheel typing + stubtest | B-10, C-14, C-27, I-01 | yes | M |
| [I-05](I-05-pr-ci-structure-caching-coverage.md) | PR CI structure, caching, coverage | B-01 | no | M |
| [I-06](I-06-largest-codegen-unit-guard.md) | Largest-codegen-unit guard (B25) | C-18, C-20, I-05 | yes | S |
| [I-07](I-07-dependencies-extras-restructure.md) | Dependencies & extras restructure | C-13, D-04, F-07, F-11, I-05 | partly (pydantic step) | M |
| [I-08](I-08-contributor-workflow.md) | Contributor workflow | C-23, I-01, I-05 | no | S |
| [I-09](I-09-import-free-docs-build.md) | Import-free docs build | C-14, C-22, G-15, I-07 | no | M |
| [I-10](I-10-diataxis-docs-skeleton.md) | Diátaxis docs skeleton, Install, Contributing | C-22, I-08, I-09 | no | L |
| [I-11](I-11-uk-ua-narrative-translation-pipeline.md) | uk_UA narrative-only pipeline (**not GA-blocking**) | I-09, I-10 | no | S |
| [I-12](I-12-deprecation-machinery-registry-ci.md) | 4.x deprecation machinery, registry CI, Deprecations page | 3x-20, A-11, B-01 | no | M |
| I-13 | *merged into 3x-20 to 3x-24, no file* | — | — | — |
| [I-14](I-14-migrate-engine.md) | `aiogram migrate` engine | A-11, G-15, I-12 | no | M |
| [I-15](I-15-receiver-inference.md) | Receiver inference (+ observer decorators) | C-26, I-14 | no | M |
| [I-16](I-16-codemod-imports-removals.md) | Rules: imports & legacy removals | C-26, G-10, G-20, I-14 | no | M |
| [I-17](I-17-model-semantics-rules.md) | Rules: model semantics | B-13, C-14, C-26, I-15 | **yes** | L |
| [I-18](I-18-positional-to-keyword-rule.md) | Rule: positional → keyword (D100) | C-26, G-11, I-15 | no | M |
| [I-19](I-19-heuristic-behaviour-rules.md) | Rules: heuristic / manual behaviour | E-03, E-07, E-09, E-11, F-03, F-11, I-14 | partly (`CallbackData` row) | M |
| [I-20](I-20-examples-port-smoke.md) | Examples port + smoke CI | E-21, F-16, G-10, H-20, I-10, I-14, I-16, I-17, I-18 | no (re-validate) | M |
| [I-21](I-21-fresh-machine-install-rehearsal.md) | Fresh-machine install rehearsal | G-15, I-01, I-02, I-03, I-04, I-07 | no | M |
| [I-22](I-22-migration-rehearsal.md) | 3→4 migration rehearsal (**exit gate**) | 3x-24, I-14, I-16, I-17, I-18, I-19, I-20, I-23 | no | M |
| [I-23](I-23-beta-pre-release.md) | 4.0 beta pre-release | C-25, D-16, E-21, F-16, G-21, H-20, I-02, I-04, I-09, I-10, I-16, I-17, I-18, I-19, I-20, I-21 | no | S |

## Order and parallel lanes

1. **Early (PD-31):** I-12 as soon as A-11 and B-01 land. I-05 right after B-01. Every story's deprecations use I-12.
2. **Build lane:** I-01 → (I-05) → I-02 → I-03 / I-21. I-06 and I-04 after C-18 / C-14. I-02 needs the full crate for
   realistic timing.
3. **Deps & docs lane:** I-07 (after D-04, F-07, F-11) → I-09 → I-10 → I-11. I-08 in parallel after C-23.
4. **Migrate lane:** I-14 → I-15 → {I-16, I-18} in parallel. I-17 after B-13 go. I-19 after E/F behaviour lands.
5. **Convergence:** I-20 → I-21 → I-23 (beta) → I-22 (exit gate) → J.

## Decide items recorded in these plans (proposed defaults, flagged to the owner)

| Item | Plan | Proposed default |
|---|---|---|
| Version source of truth | I-01 | `__meta__.py` canonical; bump script also writes Cargo.toml; equality test |
| Unsupported-platform message | I-01 | maturin's own error + Install-docs box + an `ImportError` wrapper naming the tag |
| MSRV promise | I-01 | "pinned `rust-toolchain.toml` or newer"; no "stable − 2" promise until measured |
| Release CI cost | I-02 | full matrix only on tags + weekly dry run; QEMU targets smoke-only |
| ft extras combinations | I-03 | published table per extra × {3.14t, 3.15t}; third-party gaps marked (PD-27) |
| PR vs nightly matrix | I-05 | PR: Linux cp311/cp314/cp314t + macOS/Windows cp314; rest nightly |
| "Python fallback encoder" wording (08 §5) | I-05 | stale under D1; the differential is against the 3.x oracle (A-09, PD-12); A-02 fixes the page |
| Pins violating D70 | I-07 | drop all upper caps incl. `requires-python <3.16`; keep only commented caps |
| Contributor prebuilt wheels | I-08 | not in 4.0; CI wheel artifacts for reviewers |
| `aiogram migrate` importing `_core` | I-14 | allowed (wheel installed anyway); the engine must not use it |
| 3.x signature-table version | I-15 | the migration-baseline release (3x-24) |
| Migration exit thresholds | I-22 | 0 definite false positives, ≥90% positional calls fixed with `--heuristic` |
| uk_UA GA-blocking | I-11 | not GA-blocking |
