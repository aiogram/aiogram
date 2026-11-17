# I-12 — 4.x deprecation machinery, registry CI and Deprecations page

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [A-11](../A-contracts/A-11-migration-registry.md), [B-01](../B-spike/B-01-crate-maturin-skeleton.md), [3x-20](../3x-quick-wins/3x-20-deprecation-machinery.md) |
| Blocks | [I-14](I-14-migrate-engine.md), [J-02](../J-ga/J-02-migration-guide-completion.md), [F-17](../F-fsm/F-17-fsm-docs-migration-page.md), [G-10](../G-features/G-10-utils-removals.md), [G-19](../G-features/G-19-cli-legacy-plugins.md), [D-11](../D-client/D-11-session-on-new-codec.md), [C-18](../C-butcher/C-18-rust-type-emitter.md), [C-20](../C-butcher/C-20-rust-methods-shortcuts-emitter.md) |
| Gate-conditional | no |
| Decisions | D71, D72, D82, D99, D105, PD-13, PD-31, R28 |
| Sources | [16-support-policy.md D71–D72, §1](../../research/16-support-policy.md), [18-docs-migration.md §2](../../research/18-docs-migration.md), [19 R28, "New issues"](../../research/19-review-resolutions.md), [codex-review R28](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

PD-13 makes one migration registry the source for three things: the 3.x deprecation warnings, the `aiogram migrate
check` rule ids, and the migration guide and Deprecations page. It is a data file, `aiogram/_migration/registry.toml`,
read by path so that docs and `uvx aiogram[migrate]` never import `_core`.
- A-11 owns the schema, id allocation (`AG4xxx`, append-only) and the seed.
- 3x-20 backports the machinery to 3.x.
- This plan owns the **4.x runtime machinery** and the CI and docs that read the file.

PD-31 pulls this plan ahead, because every story that deprecates something in 4.x needs the helper:
- the `model_*` aliases (D91);
- unknown fields as attributes (D105);
- session `json_loads` / `json_dumps` (PD-08);
- legacy `aiogram_cli.plugins` (D77);
- unknown kwargs (D99, a sibling category).

Today `aiogram/utils/warnings.py` only has `AiogramWarning` and `Recommendation`. The latter is removed in 4.0 (11 §3)
by E-01; this plan only coordinates.

Constraints from D72 / R28:
- the `default` filter is installed only `if not sys.warnoptions`;
- `-W error::aiogram.AiogramDeprecationWarning` is rejected by CPython ("invalid module name"), so the documented recipe
  is pytest config / `warnings.filterwarnings`;
- D99 and D105 promise **one-time** warnings, while the `default` filter means once per call site, so the machinery
  needs explicit dedupe.

Due-removal follows D71: the later of 12 months **and** 2 minor releases. CI must require an explicit decision rather
than infer one from a version (R28). This **supersedes** the 16 §1 wording "fails CI once an entry's removal version is
reached".

## Scope

**In:**
- **Warning classes.** `aiogram.AiogramDeprecationWarning(AiogramWarning, DeprecationWarning)` and its subclass
  `AiogramApiDeprecationWarning` (Bot API ledger, D72). Both are importable as `aiogram.AiogramDeprecationWarning` for
  pytest config. The module path must equal what 3x-20 backports. Alongside them, `AiogramUnknownParameterWarning`
  (D99, unknown keyword arguments forwarded at runtime), which C-20's generated constructors emit.
- **Helpers in `aiogram/_migration/__init__.py`** (the package must not import `_core`). 3x-20 lands first on
  `dev-3.x` and is merged forward with `warn_deprecated(entry_id, *, stacklevel)` and
  `deprecated_attrs(module_name, {name: (entry_id, loader)})`; this plan **adopts those names unchanged** and extends
  the package:
  - `warn_deprecated` (3x-20's), which builds the message from the registry entry: replacement and earliest removal;
  - `deprecated_attrs` (3x-20's) for module `__getattr__`;
  - `warn_once(entry_id, key=...)`, a process-wide dedupe set guarded by a `threading.Lock` (free-threading, D8);
  - `deprecated_module(entry_id)` for import-time module warnings;
  - a registration-time hook usable from `CallableObject` signature inspection (the E plans call it).
- **Lazy registry loading.** Use `tomllib` with `importlib.resources`, and only on the first warning, so there is no
  import-time cost.
- **The `default` filter** for `AiogramDeprecationWarning`, installed in `aiogram/__init__.py` only `if not sys.warnoptions`.
- **A registry CI script, `scripts/migration_registry.py check`**, which:
  - validates the file against A-11's schema;
  - checks every `warn_deprecated` / `warn_once` id used in `aiogram/` (via `ast`) exists and has kind
    `deprecation-4.x`, `removal-4.0` or `api-ledger`;
  - checks every `deprecation-4.x` entry has a test referencing its id under `tests/test_deprecations/` (16 §1, "one
    test per deprecation");
  - **due-entry rule:** reads A-11's `[entry.removal]` fields `deprecated_in` and `earliest_removal` (the later of
    12 months and 2 minors, D71). An entry is due once `earliest_removal` is reached (date passed **and** at least 2
    aiogram minors released after `deprecated_in`, from git tags). A due entry fails CI until it carries an explicit
    `removal_decision` (`remove-in = "4.N"` or `extend-until = <date>` with a reason). `removal_decision` is not in
    A-11's schema yet: this plan adds it as a schema change (A-11 owner), see the checklist.
- **The Deprecations page:** a Sphinx extension `docs/_ext/aiogram_registry.py` that reads the TOML by path and renders
  the D71 table (id, deprecated in, earliest removal, replacement, kind). It also emits the per-item header anchors J-02
  uses (`AG4xxx`).

**Out:**
- The schema, ids and seed (A-11).
- 3.x warnings (3x-20 to 3x-23).
- The checker engine (I-14).
- Guide content (J-02).
- `api-ledger` entry generation (3x-23 / C-10). This plan only reads the `kind`.

## Checklist

- [ ] Warning classes (`AiogramDeprecationWarning`, `AiogramApiDeprecationWarning`, `AiogramUnknownParameterWarning`)
      in `aiogram/utils/warnings.py`, re-exported from `aiogram/__init__.py`. Do **not** remove
      `Recommendation`: E-01 owns that removal and its registry entry; this plan only keeps the module consistent
      with it (coordinate merge order).
- [ ] Extend 3x-20's `aiogram/_migration/__init__.py` (keep `warn_deprecated` / `deprecated_attrs` names and
      signatures; add `warn_once`, `deprecated_module`, the registration hook). No `_core` import; tested by importing
      with `_core` blocked through a `sys.modules` stub.
- [ ] Schema change (A-11 owner): add the optional `removal_decision` field under `[entry.removal]` to A-11's schema
      and validator, recorded in A-11's Notes.
- [ ] Filter install plus an **ordering test matrix** run in subprocesses:
      - no options: the filter is installed and the warning is shown once per call site;
      - `-W error`: an exception is raised and our filter is not installed;
      - `PYTHONWARNINGS=ignore`: nothing is shown;
      - `-W error::DeprecationWarning`: an exception is raised;
      - pytest `filterwarnings = ["error::aiogram.AiogramDeprecationWarning"]`: an exception is raised.
- [ ] `warn_once` concurrency test: N threads, one warning (runs on 3.14t in I-03's job).
- [ ] `scripts/migration_registry.py check` plus a CI step in `make lint`. Unit tests with fixture TOML files covering
      due / not due / decided / unknown id / missing test.
- [ ] Sphinx extension plus a fixture-based test that renders a table from a small TOML.
- [ ] Docs:
      - a "Deprecation policy" section (D71: one window, removals in minors, the 4.0 reset is an explicit exception);
      - how to escalate or silence warnings (pytest config / `warnings.filterwarnings`, never `-W error::aiogram…`).
- [ ] Tests (100% coverage of `aiogram/_migration/` and the script).
- [ ] Changelog fragment `CHANGES/<id>.feature.rst` (`AiogramDeprecationWarning`, Deprecations page).
- [ ] Migration-registry entry: `Recommendation`-warning removal is E-01's (no new entry here unless A-11's seed lacks it).

## Acceptance criteria

- The ordering-matrix tests pass on cp311 and cp314 (and 3.14t via I-03).
- With today's date mocked past a fixture entry's `earliest_removal` and two minor tags after `deprecated_in`, `check`
  fails with "due: needs removal_decision". With the date one month before `earliest_removal`, it passes.
- `from aiogram import AiogramUnknownParameterWarning` works.
- An `ast`-found id missing from the registry fails `check`.
- The Deprecations page renders in the import-free docs build (I-09) from the real registry file.
- Importing `aiogram._migration` with `aiogram._core` blocked succeeds, and `warn_deprecated` / `deprecated_attrs`
  keep 3x-20's signatures.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Registry as `registry.py` imported by docs/CLI | Import pulls `_core`; data file read by path | PD-13 (revises 18 §2) |
| Separate registries for 4.x deprecations and 4.0 removals | One registry, kinds | PD-13 |
| Failing CI once a removal version is reached | Time **and** release condition; explicit decision required | D71, R28 |
| Plain `DeprecationWarning` | Hidden outside `__main__`; aiogram subclass with `default` filter | D72 |
| Documenting `-W error::aiogram.AiogramDeprecationWarning` | CPython rejects the module path | 19 "New issues", D72 |
| Installing the filter unconditionally | Would override explicit user policy | R28 |

## Validation

```bash
make dev
uv run pytest tests/test_deprecations tests/test_migration -q
uv run pytest tests
uv run mypy aiogram
uv run python scripts/migration_registry.py check
make lint
uv sync --group docs --no-install-project && uv run --no-sync bash -c 'cd docs && make html SPHINXOPTS=-W'
```

## Workflow notes

- Inputs: A-11 (schema, seed); 3x-20 (merged-forward `aiogram/_migration/__init__.py` with `warn_deprecated` and
  `deprecated_attrs`).
- Outputs:
  - `warn_deprecated` / `warn_once` / the registration hook, used by every plan that deprecates something in 4.x
    (D-11 session json params PD-08, G-19 legacy plugins, C-18 — which also replaces B-05's D105 spike shim and
    wires the `model_*` aliases, D91 — all list this plan in *Depends on*);
  - `AiogramUnknownParameterWarning` (D99), emitted by C-20's generated constructors;
  - the registry loader, used by I-14;
  - anchors, used by J-02.
- A schema change (such as `removal_decision`) is made through this plan's checklist item, owned by A-11's owner and
  recorded in A-11's Notes.
- Docs wiring: if I-09 isn't done, test the extension standalone; I-09 registers it.

## Notes

- Coordinator default (reconciliation, K10/K19/K20): no C-10 dependency (this plan only reads the `api-ledger` kind);
  3x-20's `warn_deprecated` / `deprecated_attrs` names are adopted unchanged; `removal_decision` is added to A-11's
  schema through this plan's checklist; `AiogramUnknownParameterWarning` (D99) is defined here.
