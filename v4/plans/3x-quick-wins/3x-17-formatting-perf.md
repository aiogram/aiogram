# 3x-17 — Formatting performance (`Text.render`, `_unparse_entities`) and the entity reference corpus

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-04](../A-contracts/A-04-pinned-corpus.md) (corpus location and manifest format), [A-05](../A-contracts/A-05-bench-harness.md); external prerequisite: the text-decoration escaping fix (#1979, released in 3.32.0) and PR #1919 (same-offset entity nesting) merged first |
| Blocks | [D-17](../D-client/D-17-rust-entity-rendering-kernel.md), [G-08](../G-features/G-08-formatting-on-kernel.md) |
| Gate-conditional | no |
| Decisions | PD-15 (the Rust entity kernel D-17 is parity-tested against this reference) |
| Sources | [09 #19, #20](../../research/09-3x-quick-wins.md), [06 §1](../../research/06-utils.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

- `Text.render` (`aiogram/utils/formatting.py`) re-encodes text to UTF-16 at every nesting level to compute offsets
  (`len(value.encode("utf-16-le")) // 2`). Returning the UTF-16 length from each child removes that, for an
  expected ≈20–30% gain.
- `TextDecoration._unparse_entities` (`aiogram/utils/text_decorations.py`) is O(n²) over nested entities; a
  single-stack pass makes it O(n). The same function in `formatting.py` (`_unparse_entities`) needs the same check.
- 06 §1: the Python implementation is **the reference** for the 4.0 Rust kernel's parity tests (D-17, PD-15). This
  plan therefore also publishes a corpus of entity layouts with the expected output.

## Scope

**In:**
- Internally, `Text.render` returns `(text, entities, utf16_length)`, and the public return shape stays unchanged.
  Every node type (`Text`, `Bold`, …, `TextLink`, `CustomEmoji`, `ExpandableBlockQuote`) is updated.
- Single-pass stack `_unparse_entities` for HTML and MarkdownV2, in both modules if both carry an implementation.
- **Entity reference corpus** at `benchmarks/corpus/entities/`, in A-04's format:
  - cases: nested, overlapping, same-offset, surrogate pairs, empty first node (regression case), URLs needing
    escaping;
  - for each case: input `text` + `entities`, and the expected `html_decoration.unparse` and
    `markdown_decoration.unparse` outputs;
  - each file gets a sha256 entry in the manifest.

**Out:**
- Escaping fixes: #1979 (external, already released).
- The 4.0 formatting API: G-08 / G-09.

## Checklist

- [ ] Confirm #1979 and PR #1919 are merged. Otherwise set `Status: blocked`, because the output would change
      under this plan's corpus.
- [ ] Baseline with A-05 on `formatting.nested` (a 5-level `Text` tree) and `entities.unparse` (100 entities, nested
      and overlapping).
- [ ] Implement both changes.
- [ ] Generate the reference corpus with the **parent commit's** implementation. This PR must not change outputs,
      except for documented bug fixes. Record a regeneration script under `benchmarks/corpus/entities/` (or in
      A-04's tooling).
- [ ] Tests:
  - the corpus round-trips through both decorations with identical output;
  - a property test with random nested entities (seeded, stdlib `random`) produces the same output as the old
    algorithm, which is kept in the test as the oracle.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.misc.rst`.
- [ ] Migration registry: no entry.

## Acceptance criteria

- A-05 `compare` against the parent commit:
  - `formatting.nested` median ≥ 15% faster;
  - `entities.unparse` with 100 nested entities ≥ 3× faster.
- Corpus outputs are identical before and after.
- The corpus has ≥ 50 cases, including surrogate pairs and same-offset nesting.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Move unparse to Rust in 3.x | 4.0 data plane (D-17) | D5, PD-15 |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases formatting.nested,entities.unparse
```

## Workflow notes

- **Output:** `benchmarks/corpus/entities/` is consumed by D-17 (the Rust kernel parity test) and G-08.
- It is merged forward to `dev-4.x` (PD-12).

## Notes
