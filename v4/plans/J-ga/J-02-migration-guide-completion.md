# J-02 — Migration guide completion

| Field | Value |
|---|---|
| Status | `todo` |
| Story | J — GA |
| Target branch | `dev-4.x` |
| Depends on | [I-10](../I-distribution/I-10-diataxis-docs-skeleton.md), [I-12](../I-distribution/I-12-deprecation-machinery-registry-ci.md), [I-22](../I-distribution/I-22-migration-rehearsal.md), [F-17](../F-fsm/F-17-fsm-docs-migration-page.md), [G-20](../G-features/G-20-aiogram-i18n-final-release.md), [C-26](../C-butcher/C-26-removal-inventory-signature-table.md) |
| Blocks | [J-07](J-07-ga-cut-rtd-switch.md) |
| Gate-conditional | no |
| Decisions | D82, D74, D25, D20, D71, PD-13, R28 |
| Sources | [18-docs-migration.md §2](../../research/18-docs-migration.md), [16-support-policy.md §2](../../research/16-support-policy.md), [README breaking changes](../../research/README.md), [11-removals.md](../../research/11-removals.md), [codex-review R28](../../research/codex-review.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D82 defines the guide as:
- a **checklist start page** ordered by impact;
- **per-area pages**;
- items whose headers are generated from the registry (PD-13), so the guide, the 3.x warnings (3x-20 to 3x-23) and
  `aiogram migrate check` never disagree.

I-10 created the page stubs. I-12 renders registry anchors. Story plans wrote their own area content (e.g. F-17 FSM
page, G-20 `aiogram_i18n` mapping). This plan completes, unifies and verifies the guide. R28 asks for honest limits:
the guide states what the tools can't do.

## Scope

**In:**
- **Start page.**
  - Opens with "run `aiogram migrate check`, then `aiogram migrate fix`", with the `uvx --from 'aiogram[migrate]>=4'`
    invocation against an unchanged 3.x tree.
  - A checklist ordered by impact. Each line shows codemod coverage ✔ / partial / ✖ (from the registry), the checker id
    and the finding class.
  - The I-22 coverage summary table.
- **Per-area pages** (18 §2): types & models, dispatcher & runtime, filters, middlewares & DI, FSM & scenes, errors,
  Bot client & session, utils & formatting, i18n, packaging & Python support. Each item has: what changed · why ·
  before/after code · codemod coverage · checker id · finding class · decision id.
- **Behaviour-change section** (manual checklist):
  - isolation on by default + `release_isolation` (D28, D110, PD-26);
  - sync filters inline (D34);
  - late registration and `runner.refresh()` (D114);
  - skip semantics;
  - skipped outer middlewares (D111);
  - error bubbling (D48, PD-05).
- **Packaging page:**
  - Rust needed for sdist;
  - Tier 1 / best-effort;
  - ft support table;
  - removed extras (`docs`, `cli`);
  - pydantic no longer installed transitively;
  - Python floor and the 3.11 drop in a 4.x minor (D20), stated prominently (R28).
- **External packages:** `aiogram_i18n` → core i18n mapping (link G-20's page). `aiogram-cli` → built-in CLI, with
  `pip install --force-reinstall aiogram` for broken upgrades (R30).
- **Uncovered-item check:** a script asserts every registry entry of kind `removal-4.0` has a guide item and vice versa.

**Out:**
- Writing area content another story already wrote. Edit it for consistency only.
- Release notes (J-04).

## Checklist

- [ ] Fill the start page from the registry (generated table) plus prose.
- [ ] Review each per-area page against the registry. Fill missing items with before/after code taken from I-20 /
      I-22 diffs where possible.
- [ ] Behaviour-change section with a runnable example per item (literalinclude from `examples/` or tested doc snippets).
- [ ] Packaging page.
- [ ] `scripts/migration_registry.py guide-check`: every `removal-4.0` id appears exactly once as a guide anchor
      (extends I-12's script).
- [ ] Translate-ready: narrative pages are in the I-11 extraction set (translation not GA-blocking).
- [ ] Docs build green in the import-free job (`-W`).
- [ ] Changelog fragment `CHANGES/<id>.doc.rst` (3 → 4 migration guide).

## Acceptance criteria

- `guide-check` passes: one guide item per `removal-4.0` registry entry, and none orphaned.
- Every before/after snippet either is a `literalinclude` of a tested file or is compiled by a docs test.
- The start page's coverage table equals I-22's REPORT summary (generated, no hand copy).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| One long page like `migration_2_to_3.rst` | Checklist plus per-area pages | D82 |
| Hand-maintained item list | Generated from the registry | PD-13, D82 |
| Promising full automation | Definite / heuristic / manual classes; honest limits | R28 |

## Validation

```bash
uv sync --group docs --no-install-project
uv run --no-sync bash -c 'cd docs && make html SPHINXOPTS=-W'
uv run python scripts/migration_registry.py check
uv run python scripts/migration_registry.py guide-check
uv run pytest tests/docs -q
```

## Workflow notes

- Inputs: I-10 (stubs), I-12 (anchors), I-22 (coverage numbers), F-17 and G-20 (area content), every story's registry
  entries.
- Can start after I-23 (beta) and run in parallel with J-03. Final numbers come after I-22.

## Notes

(empty)
