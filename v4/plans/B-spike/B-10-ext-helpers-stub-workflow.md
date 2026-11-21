# B-10 — `*_ext.rs` helpers + stub workflow

| Field | Value |
|---|---|
| Status | `todo` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-01](B-01-crate-maturin-skeleton.md), [B-05](B-05-views-cache-gc-routing-keys.md) |
| Blocks | [B-13](B-13-gate-run-and-decision.md), [C-14](../C-butcher/C-14-pyi-stub-emitter.md), [C-27](../C-butcher/C-27-port-ext-helpers.md), [D-17](../D-client/D-17-rust-entity-rendering-kernel.md), [I-04](../I-distribution/I-04-installed-wheel-typing-stubtest.md) |
| Gate-conditional | no |
| Decisions | D11, D16, D102, PD-15, PD-16, PD-03 |
| Sources | [02-butcher.md §5.1, §5.2](../../research/02-butcher.md), [06-utils.md §1](../../research/06-utils.md), [08-build-release.md §2, §5](../../research/08-build-release.md), [13-aiogram-rust-review.md B10, §4](../../research/13-aiogram-rust-review.md), [codex-review.md §9](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D11 puts hand-written type helpers in Rust `*_ext.rs` impl blocks, with `.pyi` fragments merged into the stubs.
There is no Python facade. The spike validates that workflow on 2–3 real helpers (01 §5.3). It also measures what
codex §9 asks for: what a helper edit costs a contributor in rebuild time. 08 §2 leaves a glue-crate experiment open
for the case where that hurts.

## Scope

**In:**
- **`user_ext.rs`.** `User.full_name` and `User.mention_html(name=None)`, ported from 3.x `aiogram/types/user.py`,
  with `html.escape` parity.
- **`message_ext.rs`.** `Message.html_text`, ported from 3.x `Message.html_text` / `_unparse_entities` in
  `aiogram/types/message.py` over `TextDecoration.unparse` in `aiogram/utils/text_decorations.py`.
  - It needs a **minimal** HTML unparse over the Rust entity list with native UTF-16 offsets: a single stack pass,
    and only the entity types present in the parity corpus.
  - The full entity kernel is **D-17** (PD-15), which replaces this code.
  - `message_ext.rs` also hosts B-09's `answer`.
- **Placement.** Separate `#[pymethods] impl` blocks through PyO3's `multiple-pymethods` feature, in
  `crates/aiogram-core/src/types/<type>_ext.rs`. A name collision with a generated member must fail compilation (one
  test shows it).
- **Stubs.** Each `<type>_ext.rs` has a sibling `<type>_ext.pyi` fragment. The spike `aiogram/_core.pyi` contains each
  fragment's text verbatim; automated merging is **C-14**.
- **Typing checks.** `stubtest` over `aiogram._core`, and `assert_type` checks run against the **installed wheel**
  from outside the repo (13 B10).
- **Contributor-cost measurement.** Incremental `maturin develop` (debug and release) after touching
  `user_ext.rs`, the cold build time, and the `.so` size, recorded for B-13.

**Out:**
- Porting the remaining ≈26 helpers (C-27, PD-16).
- MarkdownV2 unparse and the full entity kernel (D-17); `Text` formatting (G-08).
- Generated stubs and fragment merging (C-14). Installed-wheel typing CI across the matrix (I-04).

## Checklist

- [ ] Enable `multiple-pymethods`; add `user_ext.rs` and `message_ext.rs` with their `.pyi` fragments.
- [ ] Port `User.full_name` and `User.mention_html`, with parity tests against 3.x output on names that include `<`,
  `&`, quotes and non-BMP characters.
- [ ] Minimal Rust HTML unparse for `Message.html_text`. Parity tests against 3.x `html_decoration.unparse` on the
  entity-layout corpus from 3x-17 (nested, overlapping, surrogate pairs, `expandable_blockquote`, custom emoji), or
  on the A-04 corpus if 3x-17 hasn't landed.
- [ ] A compile-fail test (trybuild or equivalent `cargo test`) for a helper whose name collides with a generated
  field.
- [ ] `_core.pyi` with the fragment text; `stubtest aiogram._core` passes; `assert_type` file run against the
  installed wheel from a temp directory outside the repo.
- [ ] Record the rebuild-time and size numbers in Notes in the B-02 run-record format.
- [ ] Decide whether to run the 08 §2 glue-crate experiment (proposed default: no, unless the incremental debug
  rebuild after a helper edit exceeds 30 s on the A-05 reference host. Note that a 12-type crate doesn't extrapolate
  to ≈665 classes, so I-06 re-measures). Record in Notes and flag to owner.
- [ ] Tests in `tests/test_core/` (100% of new Python).
- [ ] No changelog or registry entry (not wired, PD-03).

## Acceptance criteria

- `mention_html` and `html_text` outputs equal 3.x on 100% of the parity corpus.
- `stubtest aiogram._core` passes with no allowlist entries for the ext members.
- `assert_type(user.mention_html(), str)` type-checks against the installed wheel (mypy run outside the repo).
- The collision compile-fail test fails compilation as expected.
- Incremental rebuild and size numbers are recorded in Notes.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Python helpers attached to native classes at import (aiogram_rust, 4 974 lines) | One language per type, native speed | D11, 13 §4 |
| pyo3-stub-gen / PyO3 experimental stub generation | Experimental; stubs come from the IR plus fragments. Re-probed for the hand-written `_core` surface only (PD-36): inspect types everything `Any` and adds no imports, pyo3-stub-gen adds 70 crates and pins pyo3; `_core.pyi` stays hand-written, checked by stubtest | 02 §5.1, 13 §2, PD-36 |
| Regions / merge markers in generated files | Generated Rust is always fully regenerated | 02 §5.1 |
| A glue crate by default | One crate (D102); measured only if rebuild cost hurts | D102, 08 §2 |
| Porting the full entity kernel here | Owned by D-17 | PD-15 |

## Validation

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
make dev
uv run pytest tests
uv run mypy aiogram
uv run python -m mypy.stubtest aiogram._core
make lint
```

## Workflow notes

- Inputs: B-05 views; the 3x-17 reference corpus (optional) or A-04.
- Outputs: the `*_ext.rs` + `<type>_ext.pyi` convention for C-14 and C-27; the seed HTML unparse for D-17 to
  replace; rebuild-time numbers for B-13 and I-06.
- Can run in parallel with B-06..B-09.

## Notes
