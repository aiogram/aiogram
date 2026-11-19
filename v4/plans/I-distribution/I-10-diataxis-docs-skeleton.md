# I-10 — Diátaxis docs skeleton, Install and Contributing pages

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-09](I-09-import-free-docs-build.md), [I-08](I-08-contributor-workflow.md), [C-22](../C-butcher/C-22-docs-rst-emitter.md) |
| Blocks | [I-11](I-11-uk-ua-narrative-translation-pipeline.md), [I-20](I-20-examples-port-smoke.md), [J-02](../J-ga/J-02-migration-guide-completion.md), [F-17](../F-fsm/F-17-fsm-docs-migration-page.md), [H-18](../H-testing-observability/H-18-toolkit-docs.md), [I-23](I-23-beta-pre-release.md) |
| Gate-conditional | no |
| Decisions | D80, D81, D82, D119, PD-27, R29 |
| Sources | [18-docs-migration.md §1–2](../../research/18-docs-migration.md), [08-build-release.md §4, §8](../../research/08-build-release.md), [11-removals.md §7](../../research/11-removals.md), [07-free-threading.md](../../research/07-free-threading.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The 3.x docs are organised by module:
- `docs/dispatcher/**`, `docs/utils/**`, `docs/api/**`;
- `docs/install.rst`, `docs/contributing.rst`;
- a 1 527-line `docs/migration_2_to_3.rst`;
- `docs/dispatcher/class_based_handlers/` (removed in 4.0, D42).

D80 restructures them along Diátaxis lines (18 §1), so every story has a place for its concept and how-to pages and the
migration guide (D82) has its own section. This plan builds the tree and the pages no other story owns.

## Scope

**In:**
- Top-level toctree in `docs/index.rst`:
  - **Install**;
  - **Tutorial** (first bot → keyboards & callbacks → FSM → i18n → testing → deploying);
  - **Concepts**;
  - **How-to**;
  - **Reference** (autoapi from I-09 + CLI);
  - **Migration 3 → 4**;
  - **Deprecations**;
  - **Changelog**, **Contributing**, **Internals**.
- Placeholder pages with a `.. note:: owned by <plan id>` for every Concepts / How-to topic listed in 18 §1, so owners
  replace them instead of inventing paths. Topic → owner map:

  | Topic | Owner |
  |---|---|
  | Runner & sources | E-13 / E-15 / E-16 |
  | Routing & snapshots | E-03 |
  | Filters | E-07 / E-08 |
  | Middlewares | E-06 |
  | DI / Depends | G-02 |
  | FSM & typed data | F-17 |
  | Scenes | F-13 |
  | i18n | G-03 |
  | Errors | E-11 |
  | Observability | H-08 |
  | Testing | H-18 |
  | Forward compatibility | E-14 |
  | Free-threading | E-19 |
  | Commands sync | G-12 |
  | Retries / rate limits | G-13 / G-14 |
  | Multi-bot | E-23 |
  | Custom storage | F-05 |
  | Custom update source | E-13 |
  | OpenTelemetry | H-08 |
  | Token safety | H-02 |
- **Install page, written here:**
  - wheels and the tier table (D119, text from I-02);
  - the "no wheel for your platform" box (I-01 decision);
  - extras (08 §8, final list from I-07);
  - the free-threaded support table (I-03);
  - building from source (Rust ≥ the pinned toolchain).
- **Contributing page** from I-08. **Internals** links the research pages as ADRs.
- Move `migration_2_to_3.rst` out of the 4.x tree (it stays in the 3.x docs, 18 §1).
- Delete `docs/dispatcher/class_based_handlers/` and the uk_UA `.po` files for removed pages on `dev-4.x`.
- Code snippets: `literalinclude` from `examples/` wherever an example exists (wired as examples land, I-20).
- Migration section stub: a start page and the 10 per-area pages listed in 18 §2. J-02 fills them.

**Out:**
- Concept and how-to content (the owners above).
- The migration guide content (J-02).
- The Deprecations page generator (I-12).
- Translation pipeline (I-11).

## Checklist

- [ ] New tree under `docs/` with `index.rst` toctrees per section. Keep URLs for still-valid 3.x pages where
      possible, and add `rediraffe`-style redirects only if already used (check before adding a dependency).
- [ ] Placeholder pages with owner notes (the topic table above).
- [ ] Write the Install page (tiers, extras, ft table, source build).
- [ ] Write Contributing and Internals.
- [ ] Remove `migration_2_to_3.rst` and `class_based_handlers/` from the 4.x tree.
- [ ] Migration section stubs: `migration/index.rst` + `types-models`, `dispatcher-runtime`, `filters`,
      `middlewares-di`, `fsm-scenes`, `errors`, `bot-client-session`, `utils-formatting`, `i18n`,
      `packaging-python-support`.
- [ ] `sphinx-build -W` green in the I-09 import-free job.
- [ ] Changelog fragment `CHANGES/<id>.doc.rst` (docs restructure). No registry entry.

## Acceptance criteria

- The import-free docs job (I-09) builds the new tree with zero warnings.
- Every topic in 18 §1 Concepts / How-to has a page (placeholder or real) and a named owner.
- The Install page lists exactly the I-07 extras and the I-02 tier table. A test compares the extras list against
  `pyproject.toml`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keeping the module-oriented 3.x layout | Diátaxis restructure | D80 |
| One-page migration guide (like `migration_2_to_3`) | Checklist plus per-area pages | D82 |
| Translating reference pages | Narrative only | D81 |

## Validation

```bash
uv sync --group docs --no-install-project
uv run --no-sync bash -c 'cd docs && make html SPHINXOPTS=-W'
uv run --no-sync pytest tests/docs -q
```

## Workflow notes

- Inputs: I-09 build, I-08 contributing text, I-01 / I-02 / I-03 / I-07 facts for the Install page.
- Outputs: the page paths every story writes into. Publish the topic → page map early; other plans' docs checklist
  items point here.

## Notes

(empty)
