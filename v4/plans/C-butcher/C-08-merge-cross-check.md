# C-08 — Merge and cross-check

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-03](C-03-html-adapter.md), [C-04](C-04-openapi-adapter.md), [C-05](C-05-errors-json-adapter.md), [C-06](C-06-overlay-schema-loader.md) |
| Blocks | [C-09](C-09-resolution-passes.md), [C-10](C-10-ledger-diff.md), [C-24](C-24-scheduled-online-reextract.md), [C-25](C-25-historical-scenario-tests.md), [H-11](../H-testing-observability/H-11-generated-toolkit-tables.md) |
| Gate-conditional | no |
| Decisions | D6a, D118, R24 |
| Sources | [02-butcher.md §2](../../research/02-butcher.md), [19 D118](../../research/19-review-resolutions.md), [codex-review.md R24](../../research/codex-review.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`build` turns the per-adapter IRs into one merged IR (02 §2):
- **Same version:** the schema is primary and the HTML is a structure check.
- **Schema lags:** the HTML decides, heuristic gaps are filled from the previous snapshot for unchanged entities, and
  the release is marked `html_only`.

R24 left two points open, and D118 doesn't close them: what "unchanged entity" means, and whether a same-version
disagreement may be resolved automatically in the schema's favour.

## Scope

**In:** `crates/butcher/src/merge.rs` and the `build` command:
- **Versions equal:** `merge(primary=openapi, structure_check=html)`. The entity, field, param and requiredness sets must
  agree.
  - A **structural** disagreement (missing or extra entity, field or param; requiredness; type shape) fails `build`
    until an overlay entry (`heuristics.toml`, C-06) pins the resolution.
  - A **heuristic** disagreement (an HTML `heuristic(rule_id)` fact vs a schema `explicit` fact) is reported as a test
    failure for that rule.
  - A **doc-only** disagreement is a warning.
- **Versions differ or OpenAPI unreachable:** `ir = html`. Heuristic gaps are filled from the previous snapshot's merged
  IR only for *unchanged* entities, the header gets `html_only = true`, and every heuristic the previous cross-check
  flagged must be resolved by the overlay.
- `errors.json` absent: reuse the previous `ir.errors.json` and note it in the manifest.
- Writes `ir.json` and the manifest fields `html_only`, overlay digest and the source sha256 values.
- A machine-readable disagreement report (`target/butcher/report.json`) for C-23 and C-24.

**Out:** D18 twins, D109 renames, union classification (C-09); the ledger (C-10).

## Checklist

- [ ] **Decide "unchanged entity"** (proposed default: the entity's IR node, with docs stripped, hashed **together with
  the transitive closure of referenced types**, param defaults, union member order and constraints, is equal to the
  same hash in the previous snapshot's `ir.html.json`; anything else counts as changed and must be decided by heuristics
  or the overlay). Record it in Notes and flag it to the owner.
- [ ] **Decide merge precedence** (proposed default: a structural discrepancy never auto-resolves and needs an overlay pin.
  The schema wins automatically only for facts the HTML can't express: int widths, encodings, constraints,
  discriminator mappings. Both facts stay in the per-adapter IRs). Record it in Notes and flag it to the owner.
- [ ] Equal-version merge with the three severity classes.
- [ ] html-only path with previous-snapshot gap fill and the `html_only` flag.
- [ ] Disagreement report JSON.
- [ ] Fixture tests: an equal-version agreement, a structural disagreement (fails), a structural disagreement resolved
  by an overlay pin, a heuristic disagreement (fails), an html-only release with one changed and one unchanged entity.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- On the fixtures, every severity class produces the documented outcome (fail / pin-resolves / warn).
- An html-only build of a new entity added on top of an unchanged previous snapshot yields `html_only = true`, and the
  new entity's facts carry `heuristic(rule_id)` provenance.
- A change in a referenced type makes the referencing entity "changed" (transitive hash test).
- `build` run twice on the same inputs yields byte-identical `ir.json` and manifest.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Schema always wins silently | A same-version disagreement doesn't prove the schema right | R24 |
| HTML-only forever | Prose heuristics drift unchecked | D6a |
| Only field-set equality as "unchanged" | Misses referenced types, defaults, union order | R24 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test -p butcher merge
cargo xtask butcher build --offline <bundle-from-C-02>
```

## Workflow notes

- Consumes C-03/C-04/C-05 outputs and C-06's `heuristics.toml`. C-09 runs on the merged IR, and C-24 reuses the
  disagreement report.

## Notes
