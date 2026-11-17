# A-11 — Migration registry: `registry.toml` schema, id allocation, seed

| Field | Value |
|---|---|
| Status | `in-progress` |
| Story | A — Contracts & baselines |
| Target branch | `dev-3.x` (merged forward; see the authority rule below) |
| Depends on | [A-01](A-01-bootstrap-dev-4x.md) (for the `dev-4.x` authority rule) |
| Blocks | [3x-20](../3x-quick-wins/3x-20-deprecation-machinery.md), [3x-21](../3x-quick-wins/3x-21-import-attribute-warnings.md), [3x-22](../3x-quick-wins/3x-22-registration-warnings.md), [3x-23](../3x-quick-wins/3x-23-mutation-ledger-warnings.md), [3x-24](../3x-quick-wins/3x-24-migration-baseline-release.md), [I-12](../I-distribution/I-12-deprecation-machinery-registry-ci.md), [I-14](../I-distribution/I-14-migrate-engine.md), [C-10](../C-butcher/C-10-ledger-diff.md), [C-26](../C-butcher/C-26-removal-inventory-signature-table.md), [D-01](../D-client/D-01-default-bot-properties-and-bot-cleanup.md), [D-02](../D-client/D-02-exceptions-error-reason-restarting-removal.md), [D-03](../D-client/D-03-token-safe-network-errors.md), [D-04](../D-client/D-04-drop-aiofiles-input-file-replayable.md), [E-01](../E-runtime/E-01-dispatcher-filter-removals.md), [E-11](../E-runtime/E-11-error-model-bubbling.md), [F-01](../F-fsm/F-01-thread-safe-memory-storage.md), [F-02](../F-fsm/F-02-isolation-lock-table-default-on.md), [F-03](../F-fsm/F-03-release-isolation-warn-after.md), [F-06](../F-fsm/F-06-redis-storage-legacy-layout.md), [F-07](../F-fsm/F-07-mongo-remove-motor-key-validation.md), [F-11](../F-fsm/F-11-callbackdata-without-pydantic.md), [G-05](../G-features/G-05-utils-i18n-compat.md), [G-10](../G-features/G-10-utils-removals.md), [G-19](../G-features/G-19-cli-legacy-plugins.md), [H-01](../H-testing-observability/H-01-logger-hierarchy.md), [3x-18](../3x-quick-wins/3x-18-unknown-union-fallback.md) |
| Gate-conditional | no (entries for gate-dependent decisions carry `gate = true`) |
| Decisions | PD-13, PD-33, D71–D74, D82, R28, PD-02 |
| Sources | [18 §2](../../research/18-docs-migration.md), [16](../../research/16-support-policy.md), [11](../../research/11-removals.md), [README breaking changes 1–24](../../research/README.md), [19 R28](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

PD-13: **one migration registry**, a data file `aiogram/_migration/registry.toml`. It is read by path (no `_core`
import), so docs builds and `uvx aiogram[migrate]` stay import-free. It feeds:
- the 3.x baseline warnings (3x-20..23);
- the 4.0 checker and codemod (I-14..I-19);
- the migration guide and the Deprecations page (I-12, J-02).

That way they can't disagree (18 §2). Ids are `AG4xxx`, append-only. Kinds: `removal-4.0`, `deprecation-4.x`,
`api-ledger` (generated). This plan fixes the schema and the id rules, and writes the seed.

## Scope

**In:**

- **Schema** (`schema = 1`), one `[[entry]]` per item:
  ```toml
  [[entry]]
  id = "AG4001"                    # append-only, never reused
  kind = "removal-4.0"             # removal-4.0 | deprecation-4.x | api-ledger
  title = "aiogram.utils.markdown is removed"
  decisions = ["D13"]              # Dxxx / PD-xx / Rxx
  area = "utils"                   # guide page (18 §2): types, dispatcher, filters, middlewares, fsm, errors, client, utils, i18n, packaging
  change = "removed"               # removed | behaviour | signature | renamed
  replacement = "aiogram.utils.formatting, or html.bold(html.quote(x))"
  detection = "definite"           # definite | heuristic | manual (R28)
  confidence = "high"              # high | medium | low
  codemod = "partial"              # full | partial | none
  suppress = "aiogram: ignore[AG4001]"
  gate = false                     # true when the item depends on the B gate (D104)
  breaking_change = 11             # README breaking-change number, if any
  generated = false                # true for api-ledger entries written by a generator
  fields = []                      # api-ledger only: removed field names of this object/method
  [entry.warn_3x]                  # 3.x baseline warning (3x-20..23); site = "none" when there is none
  site = "import"                  # import | attribute | construction | registration | class-creation | mutation | call | read | none
  target = "aiogram.utils.markdown"
  since = ""                       # filled by 3x-24 with the baseline version
  [entry.removal]                  # deprecation-4.x only (D71): deprecated_in, earliest_removal (later of 12 months / 2 minors)
  ```
  The message template is `"{id}: {title}; use {replacement}. Removed in aiogram 4.0."`, plus a docs anchor. 3x-20
  formats from it.
- **Id allocation** (PD-33):
  - `AG4001`–`AG4699` are allocated **on `dev-4.x`** by 4.0 plans;
  - `AG4700`–`AG4799` are reserved for entries first added on `dev-3.x` by 3x-20..23, so the two branches can't
    collide;
  - `AG4800`–`AG4999` are for `api-ledger` entries, **one per affected Bot API object or method** (listing its
    removed `fields`) plus one per removed entity. The research counts 122 fields in 35 files plus 3 entities, about
    40 entries.
- **Authority and sync rule** (PD-33):
  1. Before the `dev-4.x` fork, the file lives on `dev-3.x`.
  2. After the fork, `dev-4.x` is **authoritative**. `dev-3.x` changes reach it by the normal merge-forward (A-01),
     which only appends in the AG47xx and AG48xx blocks (3x-23's `api-ledger` entries) or fills `warn_3x.since`.
  3. Before each baseline-bearing 3.x release, 3x-24 copies `dev-4.x`'s file to `dev-3.x`.
  4. A test on both branches checks that the file parses, ids are unique, ids stay in their blocks, and `id` order is
     append-only against the previous release tag.
- **Seed** with one entry per item:
  - README breaking changes 1–24;
  - every 11-removals row;
  - the 16 §2 list;
  - the 3.x migration-baseline additions (3x-20..3x-24): D96 `TelegramMethod` subclasses, `UnsupportedKeywordArgument`, `Recommendation`, the
    API-ledger fields (one placeholder; 3x-23 generates the real entries), `create_channel_bot_link(parameter=)`;
  - D100 positional calls: `kind = "removal-4.0"`, `change = "signature"`, `warn_3x.site = "none"`,
    `detection = "heuristic"`, `codemod = "partial"` (PD-02, checker-only);
  - the manual-checklist behaviour items from 18 §2: D28 / D110, D34, D114, breaking change 13, D111, D48, plus D103,
    D106 and D12.

  Fill `warn_3x` for everything 3x-21..23 will implement (their scope tables), and `site = "none"` for the rest.
- **`force_reply`:** don't seed it. Bot API 10.4 made it a real field on both markups, so 11 §4 is stale. Record that
  in Notes for A-02.
- **Validation test:** `tests/test_migration_registry.py` checks the schema, unique ids, blocks, required fields per
  kind, that `decisions` are non-empty, and that each `breaking_change` 1–24 appears at least once.

**Out:**
- The 3.x reader and warnings: 3x-20..23.
- The 4.x machinery, CI due-removal check and Deprecations page: I-12.
- Checker rules: I-14..I-19.

## Checklist

- [ ] Write `aiogram/_migration/registry.toml` with the schema header comment, and `aiogram/_migration/__init__.py`
      as an empty package. The reader is 3x-20.
- [ ] Implement the PD-33 id blocks and authority rule above (owner-decided; no longer a Decide item).
- [ ] Seed every entry listed above. Cross-check the README breaking changes 1–24 and the 11 rows one by one, and list
      in Notes any item intentionally without an entry, with the reason.
- [ ] Add the validation test.
- [ ] Packaging: the file ships in the wheel (`uv build`, list the contents).
- [ ] Changelog: none yet, because nothing user-visible happens until 3x-20. Use the `skip news` label.

## Acceptance criteria

- Every README breaking change 1–24 maps to at least one entry.
- Every 11-removals row maps to an entry, or is listed in Notes with a reason.
- Ids are unique and sit in their blocks; the validation test passes.
- `python -c "import tomllib, pathlib; tomllib.loads(pathlib.Path('aiogram/_migration/registry.toml').read_text())"`
  works without importing aiogram.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| `aiogram/_migration/registry.py` | Importing it imports aiogram (and `_core` in 4.0) | PD-13 (revises 18 §2) |
| One id per API-ledger field (≈125 ids) | Bloats the checker and the guide; one id per object with a field list is enough | PD-33 |
| Separate registries for 3.x warnings and the 4.0 checker | They would disagree | 18 §2, PD-13 |

## Validation

```bash
uv run pytest tests/test_migration_registry.py -q
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv build && unzip -l dist/aiogram-*.whl | grep registry.toml
```

## Workflow notes

- **Outputs:** the schema, id rules, authority rule and seed. 3x-20 reads the file. I-12 builds the 4.x machinery and
  the CI due-removal check on it. I-14 uses the ids as checker ids. J-02 uses them as guide anchors.
- Every 4.0 plan with a user-visible break adds or adjusts its entry on `dev-4.x` (PD-13).

## Notes
