# Story 3x — 3.x quick wins & migration baseline

**Branch:** `dev-3.x`.

**Goal:** ship the pure-Python fixes from [09](../../research/09-3x-quick-wins.md) as small PRs, as reworked by D120
and PD-28. Each PR is measured against its own baseline with the A-05 harness. Together they become the honest
"optimised 3.x" that the B spike must beat (A-06). The story also delivers the **migration-baseline 3.x release**
(D74, R28): every 4.0 removal warns, and later 3.x releases keep those warnings.

**Exit gate:**
- every merged quick win has an A-05 before/after record;
- the routing, request and model oracles (A-08..A-10) show no unapproved difference;
- the baseline release is cut (3x-24).

**Baseline version name:** _to be fixed when 3x-20 starts (see 3x-24)_.

## Tasks

| ID | Title | Depends on | Gate-cond. | Size |
|---|---|---|---|---|
| [3x-01](3x-01-polling-poison-isolation.md) | Polling: isolate poison updates | A-03, A-05 | no | M |
| [3x-02](3x-02-webhook-poison-200.md) | Webhook: poison update → log + 200 | A-03 | no | L |
| [3x-03](3x-03-magicfilter-inline.md) | `MagicFilter` inline + `blocking(fn)` backport | A-05, A-10 | no | M |
| [3x-04](3x-04-keyboard-builder-add.md) | `KeyboardBuilder` O(n²) `add()` | A-05 | no | S |
| [3x-05](3x-05-memory-storage-get.md) | `MemoryStorage` reads without records | A-05 | no | S |
| [3x-06](3x-06-isolation-lock-pruning.md) | `SimpleEventIsolation` lock pruning | A-05 | no | M |
| [3x-07](3x-07-drop-model-rebuild-loop.md) | Drop import-time `model_rebuild` loop | A-05 | no | M |
| [3x-08](3x-08-butcher-literal-tags.md) | Butcher `Literal["x"]` tags; #8 measure-or-drop | A-04, A-05, A-08 | no | M |
| [3x-09](3x-09-json-request-body.md) | JSON request body without files | A-05, A-09 | no | M |
| [3x-10](3x-10-webhook-json-reply.md) | Webhook JSON reply without files | 3x-02, 3x-09, A-09 | no | S |
| [3x-11](3x-11-prebuilt-middleware-chains.md) | Prebuilt middleware chains + topology epoch | 3x-03, A-05, A-10 | no | M |
| [3x-12](3x-12-small-dispatch-costs.md) | Small dispatch costs | 3x-11, A-05 | no | S |
| [3x-13](3x-13-deserialize-no-ssl-context.md) | `deserialize_telegram_object` without SSL ctx | A-05 | no | S |
| [3x-14](3x-14-callback-data-prefix-fast-fail.md) | `CallbackData` prefix fast-fail | A-05 | no | S |
| [3x-15](3x-15-dp-update-root-filters.md) | `dp.update` root filters + filter-correctness bundle | — | no | M |
| [3x-16](3x-16-redis-update-data.md) | Redis one-RTT `update_data` — **dropped** (PD-28) | — | no | — |
| [3x-17](3x-17-formatting-perf.md) | Formatting perf + entity reference corpus | A-04, A-05 | no | M |
| [3x-18](3x-18-unknown-union-fallback.md) | `Unknown` fallback for unions (optional) | 3x-01, 3x-02, A-08, A-11 | no | L |
| [3x-19](3x-19-token-leak-fix.md) | Token leak ANT-2026-4GL80S7S | — | no | M |
| [3x-20](3x-20-deprecation-machinery.md) | Deprecation machinery backport | A-11 | no | M |
| [3x-21](3x-21-import-attribute-warnings.md) | Import/attribute warnings | 3x-20, A-11 | no | L |
| [3x-22](3x-22-registration-warnings.md) | Registration/class-creation warnings | 3x-20, 3x-21, A-11 | no | M |
| [3x-23](3x-23-mutation-ledger-warnings.md) | Mutation + API-ledger field warnings | 3x-20, A-05, A-11, C-26 | no | L |
| [3x-24](3x-24-migration-baseline-release.md) | Cut the migration-baseline release | 3x-20, 3x-21, 3x-22, 3x-23, A-11, C-26 | no | M |

None of the tasks is gate-conditional: 3.x never depends on the B spike.

## External prerequisites (3.x fixes, not plans)

- Text-decoration escaping (#1979, released in 3.32.0) and PR #1919 (nested entity rendering): needed before 3x-17.
- FSM storage atomicity: replaces 3x-16.
- Webhook background-task drain on shutdown.

3x-02, 3x-15 and 3x-19 shipped in 3.33.0; 3x-02's further external prerequisite is listed in that plan.

## Recommended order and lanes

1. **Security lane (done, shipped in 3.33.0):** 3x-19, 3x-15, 3x-02.
2. **Robustness lane, after A-03 sign-off:** 3x-01 → 3x-02 → 3x-10 (after 3x-09).
3. **Performance lane, after A-05 exists; each PR measured against its parent:**
   - Dispatch, serial, because they touch the same files: 3x-03 → 3x-11 → 3x-12.
   - Independent: 3x-04, 3x-05 + 3x-06, 3x-07, 3x-09, 3x-13, 3x-14.
   - Codegen, serial: 3x-08 → (3x-18 optional).
   - Formatting: 3x-17, after PR #1919.

   When the baseline-relevant set lands (3x-01, 03, 07, 08, 09, 11, 12, 14), A-06 tags "optimised 3.x".
4. **Migration-baseline lane, after A-11:** 3x-20 → then 3x-21 → 3x-22, with 3x-23 in parallel → 3x-24, after C-26
   freezes the removal inventory.

**Release grouping (PD-28):**
- Behaviour-changing items go into a 3.x **minor**: 3x-01, 3x-02, 3x-03, 3x-08, 3x-09, 3x-10, 3x-15, 3x-18, 3x-20..23.
- Pure fixes can go into patches: 3x-04..07, 3x-12..14, 3x-17 and 3x-19.
