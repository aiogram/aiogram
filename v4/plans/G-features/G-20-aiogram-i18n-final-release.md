# G-20 — `aiogram_i18n` → core mapping, and the final `aiogram_i18n` release

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` (mapping page) + the `aiogram_i18n` repository (final release) |
| Depends on | [G-03](G-03-i18n-core.md), [G-04](G-04-fluent-engines.md), [G-05](G-05-utils-i18n-compat.md), [G-06](G-06-lazy-text-capture.md), [G-07](G-07-lazy-filter.md), [G-09](G-09-lazy-text-trees.md) |
| Blocks | [J-06](../J-ga/J-06-external-package-releases.md), [J-02](../J-ga/J-02-migration-guide-completion.md), [I-16](../I-distribution/I-16-codemod-imports-removals.md) |
| Gate-conditional | no (the mapping page for lazy text cites G-06/G-09; if B-13 is a no-go, those rows are re-planned with them) |
| Decisions | D25, D71, PD-13 |
| Sources | [06-utils.md §3](../../research/06-utils.md), [16-support-policy.md §3](../../research/16-support-policy.md), [19 §8](../../research/19-review-resolutions.md), [README breaking change 14](../../research/README.md), [18-docs-migration.md](../../research/18-docs-migration.md) |
| Size | S (≤1 day) in this repo; external release effort tracked by J-06 |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

README breaking change 14: `aiogram_i18n` is deprecated in favour of core i18n (D25). The migration guide must map
its API **one to one**. The package gets exactly one final release carrying the deprecation notice. That release
happens in its own repository and needs a named owner and a date aligned with 4.0.0 GA (16 §3). J-06 tracks it.

## Scope

**In (this repository):**
- A docs page "Migrating from aiogram_i18n" with a table: every public `aiogram_i18n` name next to its core
  equivalent in `aiogram.i18n` (module path from G-03) or a "no equivalent, do X" note. Rows to cover:
  - `I18nMiddleware`;
  - `I18nContext`;
  - the cores (`FluentRuntimeCore`, `FluentCompilerCore`, `GNUTextCore`, or whatever the package names its gettext
    core; verify against the package source);
  - the managers;
  - `LazyProxy`;
  - `L`;
  - `LazyFilter`;
  - the `i18n` data key;
  - FSM locale storage.

  Inventory the real public API of the latest `aiogram_i18n` release before writing (record the version in Notes).
- A migration-registry entry (PD-13) for "`aiogram_i18n` deprecated, use core i18n" (kind `removal-4.0`,
  informational) and a checker hook id for I-16/I-19 (import of `aiogram_i18n` → finding + mapping link).
- The FTL-Extract note: key extraction stays external and must recognise `i18n.get`, `i18n.key()`, `L.key()`,
  `LazyFilter` (06 §3). Open an issue there if needed; record the link in Notes.

**In (external repository; executed by its owner, tracked by J-06):**
- A final release whose import emits a `DeprecationWarning` pointing to the mapping page, with a README banner.

**Out:**
- Implementing anything in `aiogram_i18n` beyond the final release.

## Checklist

- [ ] Inventory `aiogram_i18n`'s public API (version recorded in Notes).
- [ ] Mapping page (18 migration guide section).
- [ ] Registry entry + checker id.
- [ ] **Decide what the final `aiogram_i18n` release does on aiogram 4** (proposed default: it declares
      `aiogram>=3,<4` unchanged and only adds the warning; no shim over core, so there is no second implementation to
      maintain; 4.x users follow the mapping). The alternative is a thin re-export shim over `aiogram.i18n` that
      requires `aiogram>=4`. Record in Notes and flag to owner (19 §8: needs an owner in that repo).
- [ ] **Decide the owner and the release date** (aligned with 4.0.0 GA) — record in Notes and hand to J-06.
- [ ] FTL-Extract compatibility issue/link.
- [ ] Changelog fragment (`doc`).

## Acceptance criteria

- Every public name of the inventoried `aiogram_i18n` version appears in the mapping table.
- `aiogram migrate check` (I-14) on a fixture project importing `aiogram_i18n` reports the registry id with a link to
  the mapping page (verified once I-14 lands; until then, the registry entry exists and passes I-12's CI).
- J-06 has the owner, date and release checklist.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keeping `aiogram_i18n` as the recommended package | Its `LazyProxy` needs pydantic; core absorbs i18n | D25 |
| Several deprecation releases | One final release with the notice | 06 §3 |

## Validation

```bash
uv run --group docs --no-install-project bash -c 'cd docs && make html'   # R29; docs is a dependency group in 4.x (D68)
make lint
uv run pytest tests
```

## Workflow notes

- Inputs: final names from G-03..G-07 and G-09.
- Output: J-06 (external release tracking), J-02 (migration guide), I-16 (the `aiogram_i18n` import rule reports this
  plan's registry id with the mapping-page link).

## Notes
