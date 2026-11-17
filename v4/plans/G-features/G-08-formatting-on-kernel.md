# G-08 — Formatting nodes on the Rust entity kernel

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [D-17](../D-client/D-17-rust-entity-rendering-kernel.md), [3x-17](../3x-quick-wins/3x-17-formatting-perf.md) |
| Blocks | [G-09](G-09-lazy-text-trees.md), [G-11](G-11-generated-utils-signatures.md) |
| Gate-conditional | no (uses only the D-17 kernel functions and public `MessageEntity` constructors; the `Message.html_text` fast path lives in C-27 / B-10) |
| Decisions | D62, D5, PD-15, D13 |
| Sources | [06-utils.md §1, §4](../../research/06-utils.md), [09-3x-quick-wins.md #19, #20](../../research/09-3x-quick-wins.md), [plans README §1 PD-15](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D62 makes `aiogram.utils.formatting` the primary style. It is entity-based, so there are no escaping bugs, and it
works with lazy i18n (D61, G-09).

PD-15 puts the Rust kernel (UTF-16 math, HTML / MarkdownV2 unparse, quoting) in the data plane (D-17). This plan
moves the Python API onto that kernel:
- `Text.render` stops re-encoding at every nesting level (06 §1: 0.74 µs per 300 chars, recomputed per level);
- the built-in decorations use the Rust unparse (HTML 22 µs, MarkdownV2 33 µs today at 230 chars / 6 entities).

## Scope

**In:**
- `aiogram/utils/formatting.py`:
  - `Text.render` uses the D-17 UTF-16 length/offset functions instead of `sizeof()` re-encoding. `sizeof` stays as
    a public helper on the kernel.
  - `as_html()` / `as_markdown()` call the kernel for the built-in decorations.
- `aiogram/utils/text_decorations.py`: the **extensibility rule** (06 §1):
  - only the exact built-in instances `html_decoration` and `markdown_decoration` (and exact built-in classes) take
    the Rust fast path;
  - any `TextDecoration` subclass runs the Python algorithm, which is the O(n) single-stack-pass reference from 3x-17
    (09 #20), merged forward.
- **Parity corpus usage**: the 3x-17 reference corpus (nested, overlapping, surrogate pairs, `expandable_blockquote`,
  custom emoji, `date_time`) runs against both the Rust kernel and the Python reference in one parametrised test.
  Any difference fails.
- `Text.as_kwargs()` and the hand-written `as_*_kwargs` keep working. Their generated replacement is G-11.
- **Docs (D62)**: the formatting page leads; html/md decorations are documented as supported for `parse_mode` users
  and for `html_text` / `md_text`. Remove `utils.markdown` from navigation (its removal is G-10).

**Out:**
- The Rust kernel itself: D-17.
- `Message.html_text` / `md_text` / `MessageEntity.extract_from` on Rust types: C-27 / B-10.
- HTML / MarkdownV2 **parse** (string → entities): dropped from 4.0 (PD-15).
- Lazy values in `Text`: G-09.

## Checklist

- [ ] Rewire `Text.render` and decorations to D-17. Keep the public signatures of `aiogram.utils.formatting` and
      `aiogram.utils.text_decorations` unchanged (diff against `dev-3.x` `__all__`).
- [ ] Fast-path selection by exact type (`type(deco) is HtmlDecoration`), with a test that a subclass overriding
      `bold` produces its own output.
- [ ] Parity test over the 3x-17 corpus (Rust vs Python reference), plus a hypothesis-style generated test if the
      corpus has a generator (no new dependency; otherwise skip).
- [ ] Benchmarks via the A-05 harness: `Text.render` and `as_html` on the pinned 230-char / 6-entity input from 06 §1.
- [ ] Docs restructure for D62.
- [ ] Tests (100% coverage of new code).
- [ ] Changelog fragment (`misc`/perf). No migration-registry entry, because behaviour is identical.

## Acceptance criteria

- The parity corpus yields identical HTML, MarkdownV2 and entity lists for Rust and Python.
- On the pinned 06 §1 input (230 chars, 6 entities), `html_decoration.unparse` is **≤ 5 µs** and MarkdownV2 **≤ 7 µs**
  (today 22 / 33 µs). `Text.render` on the same tree is at least **2×** faster than the 3x-17 optimised baseline (A-06
  records it). Thresholds are re-checked against D-17's own bench; if D-17 records different achievable numbers,
  use those and note it.
- A `TextDecoration` subclass never reaches the Rust path (asserted with a spy).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Rust kernel owned by G | Data plane per D5; consumers are `message_ext.rs` and the encoder | PD-15 |
| Rust fast path for subclasses | Would bypass user overrides of `bold` / `link` / `quote` | 06 §1 |
| HTML/MarkdownV2 parse in Rust for 4.0 | No 4.0 consumer; the fake's parser stays Python | PD-15 |
| Dropping html/md decorations | `parse_mode` users and `html_text` need them | D62 |

## Validation

```bash
cargo fmt --check && cargo clippy -- -D warnings && cargo test
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: D-17 kernel API (record the exact function names D-17 exposes in Notes); 3x-17 corpus + Python reference
  (merged forward via A-01's sync policy).
- Outputs: G-09 (lazy `Text`), G-11 (generated `as_*_kwargs` bodies), and I-16 (codemod `utils.markdown` →
  formatting needs this API stable).

## Notes
