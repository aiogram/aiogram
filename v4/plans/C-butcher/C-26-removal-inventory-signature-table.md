# C-26 — 4.0 removal inventory and 3.x signature table

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-3.x` (generated there from `.butcher/`, merged forward to `dev-4.x`; C-11 deletes `.butcher/` on `dev-4.x`) |
| Depends on | [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [I-15](../I-distribution/I-15-receiver-inference.md), [I-18](../I-distribution/I-18-positional-to-keyword-rule.md), [3x-23](../3x-quick-wins/3x-23-mutation-ledger-warnings.md), [J-02](../J-ga/J-02-migration-guide-completion.md), [3x-24](../3x-quick-wins/3x-24-migration-baseline-release.md), [I-16](../I-distribution/I-16-codemod-imports-removals.md), [I-17](../I-distribution/I-17-model-semantics-rules.md) |
| Gate-conditional | no |
| Decisions | D6c, D100, D74, R28, PD-12, PD-13 |
| Sources | [02-butcher.md §4](../../research/02-butcher.md), [11-removals.md §1](../../research/11-removals.md), [16-support-policy.md](../../research/16-support-policy.md), [18-docs-migration.md §2](../../research/18-docs-migration.md), [19 §2 R28](../../research/19-review-resolutions.md), [plans README PD-12, PD-13](../README.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Two pieces of data are needed for migration:
- **The 4.0 ledger reset** drops everything deprecated in 3.x: 122 fields in 35 files (`reply_to_message_id` ×18,
  `allow_sending_without_reply` ×18, `receiver_user_id` ×13, `callback_query_id` ×13, the 35 `Chat` fields from 7.3,
  `switch_pm_*`, …) and the types `KeyboardButtonRequestUser`, `UserShared`, `StoryAreaPosition` (11 §1). Each must be
  listed in the migration guide, warned about in the migration-baseline 3.x release (3x-23, which writes the
  `api-ledger` registry entries), and flagged by the checker (D74). This plan produces the inventory those entries are
  cross-checked against. (The request-only twin fields that C-09 drops are appended by C-09 on dev-4.x.)
- **D100's codemod** rewrites positional calls (`bot.send_message(1, "hi")`, `message.answer("hi")`) and needs the
  **3.x positional parameter order** of every generated callable. No other plan produces it.

## Scope

**In:**
- `scripts/butcher_removal_inventory.py` (a plain Python script on dev-3.x, part of the throwaway PD-10 tooling):
  reads `.butcher/**/entity.json` **directly** (no butcher, no C-11 importer) and writes
  `aiogram/_migration/data/removal_inventory_3x.json`: one record per deprecated field or entity with the entity,
  field, `removed_in` (Bot API version from `entity.json`) and the replacement where known (e.g. `reply_parameters`).
  It writes **no** registry entries: 3x-23 generates the `api-ledger` entries (AG48xx), and a cross-check test here
  asserts that every inventory record is covered by exactly one of them.
- `scripts/butcher_signatures_3x.py`: run inside the **pinned external 3.x venv** (PD-12). It uses `inspect.signature`
  over `Bot` methods, every `TelegramMethod` subclass constructor, every `TelegramObject` constructor and every generated
  shortcut, and writes `aiogram/_migration/data/signatures_3x.json` with four separate tables:
  1. **method signatures**: `Bot` methods, `TelegramMethod` and `TelegramObject` constructors —
     `{qualname: [positional params in order]}`;
  2. **shortcut signatures**, kept separate from the methods (a shortcut's own order differs from its target
     method's, I-18), each with its receiver type (I-15 receiver inference);
  3. **collection-field map**: collection (list/tuple) fields per type (I-17 collection rules, D106);
  4. **observer → event-type map**: every 3.x `Router` observer name → the event type it delivers (I-15).
- **Branch of record:** both scripts run on **dev-3.x**, where `.butcher/` still exists, so 3x-23 can ship the
  baseline warnings before 4.0; the data files are merged forward to dev-4.x. No dev-4.x tooling (cargo, butcher,
  C-09 / C-11) is needed. C-09 appends the dropped-twin entries on dev-4.x itself.
- Both files are read by path (no `_core` import, PD-13).

**Out:** the codemod and checker (I-14..I-19); registry CI and the Deprecations page (I-12); 3.x warning emission and
the `api-ledger` registry entries (3x-23); the dropped twin-field entries (C-09, dev-4.x).

## Checklist

- [ ] Inventory script reading `.butcher/**/entity.json` → `removal_inventory_3x.json`; idempotent (re-running
  produces no diff).
- [ ] Signature script in the pinned 3.x venv → `signatures_3x.json` with the four tables (methods, shortcuts
  separately, collection fields, observer → event type).
- [ ] Generate on **dev-3.x** and merge forward to dev-4.x (settled; `.butcher/` is deleted on dev-4.x by C-11).
- [ ] Test: the inventory record count equals the `entity.json` deprecation-marker count (122 fields + 3 types at 10.4).
- [ ] Cross-check test: every inventory record is listed by exactly one 3x-23 `api-ledger` entry (AG48xx, in `fields` or as a removed entity), and no `api-ledger` entry lists a name missing from the inventory.
- [ ] Test: `signatures_3x.json` contains `Bot.send_message` with `chat_id` and `text` first (methods table), and `Message.answer` with `text` first (shortcuts table, receiver `Message`).
- [ ] Test: the collection-field map lists `Message.entities`, and the observer map maps `callback_query` → `CallbackQuery`.
- [ ] Migration-registry entry: none here (3x-23 writes the `api-ledger` entries; A-11's seed has the breaking change 8 entry). Changelog: none (internal data, `skip news`); the user-facing reset fragment is 3x-23's.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- `removal_inventory_3x.json` lists every 3.x-deprecated field and type exactly once, and the cross-check against
  3x-23's `api-ledger` entries reports 0 differences (the test is written here, skipped while no `api-ledger` entries
  exist, and becomes active in 3x-23's PR).
- `signatures_3x.json` covers 100% of the 3.x `Bot` methods, method classes and shortcuts (count test against the pinned 3.x venv).
- `signatures_3x.json` has the four tables; every 3.x `Router` observer appears in the observer map.
- I-15, I-17 and I-18 can load both files without importing `aiogram._core` (test by reading them with a plain `tomllib` / `json` load).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Carry the deprecated fields as ledger entries in 4.0 | 4.0 reset | D6c |
| Derive positional order from `entity.json` + `keep_position` | Indirect; the pinned 3.x venv gives the exact runtime signatures | PD-12 |
| Registry as Python module | Data file read by path | PD-13 |

## Validation

```bash
# on dev-3.x
uv run python scripts/butcher_removal_inventory.py --out aiogram/_migration/data/removal_inventory_3x.json
uv run --python <pinned-3.x-venv>/bin/python scripts/butcher_signatures_3x.py --out aiogram/_migration/data/signatures_3x.json
git diff --exit-code aiogram/_migration/data/
uv run pytest tests/test_migration_data
make lint
```

## Workflow notes

- Consumers: I-15 (receiver inference: shortcut receivers, observer map), I-17 (collection-field map), I-18
  (positional → keyword: method and shortcut signatures), 3x-23 (baseline warnings and `api-ledger` entries, on
  dev-3.x before 4.0; cross-checked here), A-11 (schema the cross-check reads), J-02 (migration guide).

## Notes

- Coordinator default (reconciliation, K2/K3): no registry entries are emitted here; 3x-23 writes the `api-ledger`
  entries and this plan cross-checks them. The inventory is read from `.butcher/**/entity.json` on dev-3.x, so C-09 and
  C-11 are no longer prerequisites.
