# D-17 — Rust entity-rendering kernel: UTF-16 offsets, HTML/MarkdownV2 unparse and quoting

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [B-01](../B-spike/B-01-crate-maturin-skeleton.md), [B-10](../B-spike/B-10-ext-helpers-stub-workflow.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [3x-17](../3x-quick-wins/3x-17-formatting-perf.md) |
| Blocks | [G-08](../G-features/G-08-formatting-on-kernel.md), [G-09](../G-features/G-09-lazy-text-trees.md), [C-27](../C-butcher/C-27-port-ext-helpers.md) |
| Gate-conditional | yes (assumes the milestone B gate passes, D104; re-validate after B-13) |
| Decisions | PD-15, D5, D11 |
| Sources | [06-utils.md §1](../../research/06-utils.md), [02-butcher.md §5.1](../../research/02-butcher.md), [08-build-release.md §7](../../research/08-build-release.md), [plans README §1 PD-15](../README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Entity rendering is data-plane work (D5). Today (`aiogram/utils/text_decorations.py`):
`TextDecoration.unparse` / `_unparse_entities` is a recursive generator with a `filter()` sub-list per entity
(O(n²)): HTML 22 µs, MarkdownV2 33 µs for 230 chars / 6 entities. UTF-16 helpers (`add_surrogates`,
`remove_surrogates`, `aiogram/utils/formatting.py` `sizeof`) are recomputed at every nesting level (0.74 µs per 300
chars). Quoting: `html.quote` 1.4 µs, MarkdownV2 quote 4.4 µs (06 §1). With Rust-native types the entities already
live in Rust, so rendering from the Rust entity list in one stack pass is natural.

PD-15: the kernel is owned here; G-08 builds the Python formatting API (`Text`, `Bold`, `html_decoration`, …) on it.
Parsing HTML/MarkdownV2 into entities is **not** in 4.0 (no consumer; dropped from the README box).

## Scope

**In:**
- Rust module (e.g. `crates/aiogram-core/src/entities/`) exposing coarse functions through the native submodule `aiogram._core.render`:
  - `utf16_len(text) -> int`, `utf16_slice(text, offset, length) -> str`;
  - `unparse_html(text, entities) -> str`, `unparse_markdown_v2(text, entities) -> str` — same output as 3.x
    `html_decoration.unparse` / `markdown_decoration.unparse` for every entity type incl. nested, overlapping,
    surrogate pairs, `pre` with language, `text_link`, `text_mention`, `custom_emoji`, `blockquote`,
    `expandable_blockquote`, `date_time`;
  - `quote_html(text)`, `quote_markdown_v2(text)`;
  - a renderer entry for formatting trees that returns `(text, entities)` with UTF-16 offsets computed once (the
    contract G-08's `Text.render` calls; exact input shape agreed with G-08 — see Decide item).
- `Message.html_text` / `md_text` exposed from `message_ext.rs` via the D11 `*_ext.rs` + `.pyi` fragment workflow
  (B-10).
- Parity test suite against the **3x-17 reference corpus** of entity layouts, comparing the Rust kernel to the 3.x
  Python reference output.

**Out:**
- Python `TextDecoration` API, subclass fallback (subclasses run the Python algorithm, 06 §1 extensibility rule) and
  its O(n) Python rewrite → G-08.
- Lazy text in formatting trees → G-09. HTML/MarkdownV2 parsing → not in 4.0 (PD-15).
- Other hand-written helpers → C-27.

## Checklist

- [ ] UTF-16 helpers.
- [ ] HTML and MarkdownV2 unparse in one pass from the entity list.
- [ ] Quoting functions.
- [ ] Decide the formatting-tree render input shape with G-08 (proposed default: a flat pre-order list of
      `(kind, text_or_none, attrs)` nodes built in Python, one Rust call per `render()`) — record in Notes and flag
      to owner.
- [ ] `html_text` / `md_text` via `message_ext.rs` + `.pyi` fragment; stubtest clean.
- [ ] Parity suite on the 3x-17 corpus (every case byte-equal).
- [ ] Bench on the 06 §1 pinned input (230 chars, 6 entities) via B-02/A-05.
- [ ] clippy restriction lints clean.
- [ ] Tests (100% Python coverage of new code; Rust unit tests).
- [ ] Changelog fragment (`misc`: faster entity rendering).

## Acceptance criteria

- 100% of 3x-17 corpus cases produce byte-identical output to the 3.x Python reference for HTML and MarkdownV2.
- `utf16_len` matches `len(text.encode("utf-16-le")) // 2` on the corpus plus non-BMP fuzz strings.
- Bench (230 chars, 6 entities, warm, median of 7): HTML unparse ≥5× faster than 3.x (22 µs), MarkdownV2 ≥5× faster
  than 3.x (33 µs); `quote_html` and `quote_markdown_v2` each ≥3× faster than 3.x.
- `Message.html_text` on a decoded message equals 3.x output for every corpus message.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep rendering in Python only | Entities live in Rust; per-entity FFI reads cost more | 06 §1, D5 |
| Rust parse of HTML/MarkdownV2 into entities | No 4.0 consumer | PD-15 |
| Rust fast path for `TextDecoration` subclasses | Subclasses override methods; must run Python | 06 §1 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
make dev
uv run pytest tests
uv run mypy aiogram
make lint
make bench
```

## Workflow notes

- Inputs: B-10 (`*_ext.rs` + stub workflow), 3x-17 reference corpus.
- Outputs: kernel functions consumed by G-08 (formatting API), G-09 (lazy `Text` render), C-27 (remaining helpers
  that render text).
- Independent of D-01..D-16; can run in parallel after B-13.

## Notes
