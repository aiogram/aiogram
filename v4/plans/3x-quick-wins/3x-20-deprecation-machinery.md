# 3x-20 — Deprecation machinery backport (warning classes, filter, registry reader)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-11](../A-contracts/A-11-migration-registry.md) (`aiogram/_migration/registry.toml` schema, ids, seed) |
| Blocks | [3x-21](3x-21-import-attribute-warnings.md), [3x-22](3x-22-registration-warnings.md), [3x-23](3x-23-mutation-ledger-warnings.md), [3x-24](3x-24-migration-baseline-release.md), [I-12](../I-distribution/I-12-deprecation-machinery-registry-ci.md) |
| Gate-conditional | no |
| Decisions | D71, D72, D74, R28, PD-13 |
| Sources | [16 D72, §1, §2](../../research/16-support-policy.md), [18 §2](../../research/18-docs-migration.md), [19 R28](../../research/19-review-resolutions.md), [codex-review R28](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The migration-baseline 3.x release (D74, R28) warns about everything 4.0 removes or changes. 3.x has no machinery
for it yet: `aiogram/utils/warnings.py` defines only `AiogramWarning` and `Recommendation`. PD-13 makes one data file,
`aiogram/_migration/registry.toml`, the single source for:
- the 3.x warnings;
- the 4.0 checker (I-14);
- the guide and the Deprecations page (I-12).

This plan adds the 3.x side: warning classes, the filter policy, a lazy registry reader, a `warn_deprecated(id)`
helper, the module-attribute shim pattern, the test that keeps the registry and warnings in sync, and the
suite-wide "aiogram never warns about itself" guard.

## Scope

**In:**
- **Warning classes** in `aiogram/utils/warnings.py`, both exported from top-level `aiogram`:
  - `AiogramDeprecationWarning(AiogramWarning, DeprecationWarning)`;
  - `AiogramApiDeprecationWarning(AiogramDeprecationWarning)`.

  The pytest recipe `filterwarnings = ["error::aiogram.AiogramDeprecationWarning"]` must resolve.
- **Filter policy (D72, R28).** In `aiogram/__init__.py`, call `warnings.filterwarnings("default",
  category=AiogramDeprecationWarning)` **only `if not sys.warnoptions`**. Each deprecation then shows once per call
  site, also outside `__main__`.
- **Registry reader** `aiogram/_migration/__init__.py`:
  - `tomllib` over `registry.toml`, located by path relative to the package and loaded lazily on the first warning
    (`functools.cache`), so import time is unchanged;
  - `warn_deprecated(entry_id, *, stacklevel)` formats the message from the entry: `"AG4012: <title>; use
    <replacement>. Removed in aiogram 4.0. See <docs url>#ag4012"`;
  - API-ledger entries warn with the subclass.
- **Module-attribute shim helper** for removed names: `deprecated_attrs(module_name, {name: (entry_id, loader)})`,
  which returns a module `__getattr__`. aiogram's own code imports the private implementation, so it never goes
  through the shim. That pattern is what 3x-21 applies.
- **Sync test** (`tests/test_migration/`):
  - every entry with `warn_3x.site != "none"` is listed in a test table mapping id → trigger callable, and the test
    asserts the warning class and the id in the message;
  - an entry without a trigger fails the test, and so does a trigger without an entry.

  The table lives in the test file and grows with 3x-21..23. This implements 16 §1's "one test per deprecation".
- **Self-warning guard:** `pyproject.toml` `[tool.pytest.ini_options] filterwarnings` adds
  `"error::aiogram.AiogramDeprecationWarning"`. Tests that exercise deprecated APIs use `pytest.warns`.
- **Recategorise** the existing `DeprecationWarning`s in aiogram to `AiogramDeprecationWarning` when they announce a
  4.0 removal: `utils/link.py` (`create_channel_bot_link(parameter=)`), plus a grep for others. This plan does it, and
  A-11 seeds their entries.
- **A generated docs table:** `scripts/render_migration_registry.py` writes `docs/migration/registry_table.rst`,
  which the 3x-24 page includes.

**Out:**
- The individual warnings: 3x-21 (import and attribute), 3x-22 (registration and class creation), 3x-23 (mutation
  and API ledger).
- The 4.x deprecation machinery, CI due-removal checks and the 4.x Deprecations page: I-12.

## Checklist

- [ ] Add the classes and exports. Test `aiogram.AiogramDeprecationWarning` and its subclassing.
- [ ] Add the filter. Tests in subprocesses:
  - with no `-W`, a warning shows once per call site;
  - with `python -W ignore`, no output (because `sys.warnoptions` is set);
  - with `python -W error::DeprecationWarning`, the warning raises;
  - `warnings.filterwarnings("error", category=AiogramDeprecationWarning)` **after** `import aiogram` raises.
- [ ] Decide what happens to an application's code-level filter set **before** `import aiogram` (for example
      `warnings.simplefilter("ignore")`), which our front-inserted `default` filter overrides. Proposed default:
      accept it and document "set filters after importing aiogram, or use `-W` / pytest config". Record it in Notes
      and flag it to the owner (R28: "must not override an application's explicit ... policy").
- [ ] Add the registry reader and `warn_deprecated`:
  - an unknown id raises `KeyError` in tests and is a no-op in production;
  - the message format matches A-11's `message` template;
  - `stacklevel` is correct, so the warning points at user code (test with `warnings.catch_warnings(record=True)` and
    the filename).
- [ ] Add the shim helper, with a test module.
- [ ] Add the sync test and the self-warning guard. The full suite must pass with the guard enabled. Expect no
      failures here, because no warnings exist yet apart from the recategorised ones.
- [ ] Recategorise `create_channel_bot_link(parameter=)` and any other existing 4.0-removal `DeprecationWarning`
      to `warn_deprecated(<id>)`.
- [ ] Add the registry render script and its test.
- [ ] Packaging: `registry.toml` is included in the wheel. Check with `uv build` and list the wheel contents.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.feature.rst`: "`aiogram.AiogramDeprecationWarning`, shown once per call
      site by default".
- [ ] Migration registry: this plan reads the registry and adds no entries. The `create_channel_bot_link` entry
      belongs to the A-11 seed; add it here if A-11 missed it.

## Acceptance criteria

- `import aiogram` doesn't read `registry.toml` (no file access traced on import) and its import time is unchanged
  (A-05 `import.aiogram`, within noise).
- Every R28 ordering scenario above behaves as described.
- The full suite passes with `error::aiogram.AiogramDeprecationWarning` enabled.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| `aiogram/_migration/registry.py` (Python module) | Importing it would import aiogram; docs and `uvx aiogram[migrate]` must stay import-free | PD-13 (revises 18 §2) |
| Recommend `-W error::aiogram.AiogramDeprecationWarning` | CPython rejects the module path ("invalid module name") | R28 |
| Install the filter unconditionally | Overrides explicit `-W` policy | R28 |
| Plain `DeprecationWarning` | Hidden outside `__main__` by default; can't be filtered by category | D72 |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv build && unzip -l dist/aiogram-*.whl | grep registry.toml
```

## Workflow notes

- Consumes A-11's file. If A-11 changes the schema, the reader follows it.
- **Registry authority:** after `dev-4.x` diverges, 4.0 plans add entries there. 3x-24 syncs the file back to
  `dev-3.x` before each baseline-bearing release (see A-11 Workflow notes).
- 3x-21, 3x-22 and 3x-23 can run in parallel after this lands.

## Notes
