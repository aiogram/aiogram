# C-03 — HTML adapter

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-01](C-01-crate-xtask-ir-snapshot.md) |
| Blocks | [C-08](C-08-merge-cross-check.md) |
| Gate-conditional | no |
| Decisions | D6a, D118, R24 |
| Sources | [02-butcher.md §1, §2](../../research/02-butcher.md), [19 D118](../../research/19-review-resolutions.md), `.butcher/schema/schema.json` (3.x, legacy-parsed 10.4) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The HTML docs (`core.telegram.org/bots/api`) are always current, but structure has to be inferred from prose. The
OpenAPI schema lags on staging (10.3 vs 10.4 on 2026-11-16), so the HTML adapter **decides** facts for entities added
since the last schema version. Otherwise it is the structural cross-check (02 §2). Its heuristics are ported from the
legacy Python parser, and every one gets a `rule_id`, so C-08 can report heuristic-vs-schema disagreements as failures
instead of silent drift.

## Scope

**In:** `crates/butcher/src/sources/html.rs` (`scraper`), producing `ir.html.json`. It ports these legacy behaviours
(02 §1):
- walk `a.anchor` under `h3`/`h4`; an `h4` with a one-word title is an entity, a lowercase first letter means a method;
- zip tables by header. Method `required` comes from the Yes/Optional column; type `required` from the `Optional`
  prefix (replace the fixed 10-char slice with a prefix match);
- type strings: `Array of X`, `X or Y`, a capitalised word is an entity ref, `Integer`/`Float`/`String`/`Boolean`/`True`;
- return types: the 14 ordered regexes plus the 3 manual `returning` overrides (the overrides move to the overlay, C-06), each regex a `rule_id`;
- consts: the 3 regexes; subtype lists: `- (.+)` over the parent description;
- enum members: `parse`/`multi_parse` regex over field descriptions (the rules themselves come from the overlay; the adapter exposes the description text);
- `Unix time` description detection (input to the datetime warning in C-09);
- descriptions as plain / HTML / RST `Doc`;
- version and date from the first `recent-changes` `h4`;
- a preview page (`--preview`, e.g. corefork) merged as upcoming entities, flagged in the IR header.

Every inferred fact carries `heuristic(rule_id)`. Facts read straight from a table cell are `explicit`.

**Out:** int widths, multipart encodings, discriminator mappings (the HTML has none; C-04); merging (C-08).

## Checklist

- [ ] Parser for entities, methods, fields and params, including requiredness.
- [ ] Type-string parser with `rule_id`s; unknown shapes are an error that names the entity and field, never a silent `str`.
- [ ] Return-type regexes ported in order; first match wins; no match is an error unless the overlay pins it.
- [ ] Const and subtype extraction; enum-description capture.
- [ ] Preview-page merge.
- [ ] **Decide the adapter fixture policy** (proposed default: tests use **small hand-written HTML excerpts** under
  `crates/butcher/tests/fixtures/html/`, one per rule, plus one full-page parity test that runs against a cached fetch
  only when `BUTCHER_LIVE=1`. No full Telegram page is committed, per the 02 §6 license note). Record it in Notes and flag it to the owner.
- [ ] Parity test against the legacy output: every entity, field, param, requiredness and type equal to the 3.x
  `.butcher/schema/schema.json` (10.4), with an explicit approved-difference list (each with a reason). The legacy file
  is derived data already committed in 3.x; copy it as a compressed test fixture before C-11 deletes `.butcher/`.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- Parity with the legacy 10.4 schema: 0 unapproved differences across 428 types, 193 methods and their fields and params.
- Every rule has at least one fixture test, and removing a rule makes its test fail.
- An unparseable type string fails with `entity.field: unsupported type "…" (rule …)`.
- Output is byte-identical across two runs on the same cached page.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| HTML-only generation (legacy model) | Prose heuristics silently drift; the schema gives structure | D6a |
| Drop the HTML adapter, OpenAPI only | The schema lags the live API (10.3 vs 10.4) | 02 §2, §6 |
| Commit full Telegram HTML pages as fixtures | License note: commit derived data only | 02 §6, D118 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test -p butcher html
BUTCHER_LIVE=1 cargo test -p butcher html_parity -- --ignored   # with a cached fetch from C-02
```

## Workflow notes

- Parallel with C-04, C-05 and C-06. C-08 consumes `ir.html.json`.
- C-25 reuses the rule fixtures for the "historical HTML/schema disagreement" scenario.

## Notes
