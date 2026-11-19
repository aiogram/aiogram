# Story C — Reproducible butcher

**Goal.** Replace the 3.x Python legacy butcher with **butcher**, a Rust generator in `crates/butcher`, run as
`cargo xtask butcher`:
- two input adapters (HTML docs + OpenAPI 3.2 schema, plus `errors.json`) feed one IR, with committed per-adapter IRs
  and a provenance manifest (D118);
- a strict TOML overlay and a compat ledger (reset at 4.0, rolling window afterwards; D6);
- emitters for Rust types and methods, `.pyi` stubs, Python re-export modules (D16), enums and `ErrorReason`, the
  `_BotMethods` and router-observer mixins, utility signatures (D59), docs index pages and generated tests.

PR CI emits and checks **offline**; a scheduled job re-extracts online.

**Exit gate (README milestone C):** offline emit is deterministic on Linux, macOS and Windows ([C-23](C-23-check-offline-determinism.md)),
and historical diffs, a new union, a name collision and an unsupported `send_copy` content are all handled
([C-25](C-25-historical-scenario-tests.md)).

**Naming.** *butcher* is the new Rust tool. *Legacy butcher* is the 3.x Python tool, which stays on `dev-3.x` until
3.x full support ends (D73). `import-legacy` is a throwaway Python script behind the xtask shim (PD-10).

**Gate.** Adapters, IR, overlay, ledger and the Python emitters are gate-independent and can start during the B spike.
The Rust emitters, the type-stub surface, generated tests and the helper port are **gate-conditional**: they start after
[B-13](../B-spike/B-13-gate-run-and-decision.md) is a *go*. Until then, emitted Python goes to a staging tree (PD-03).

## Tasks

| ID | Title | Depends on | Gate-cond. | Size |
|---|---|---|---|---|
| [C-01](C-01-crate-xtask-ir-snapshot.md) | butcher crate, xtask, IR model, snapshot format | A-01, B-01 | no | M |
| [C-02](C-02-fetch-provenance.md) | `fetch`, source cache, manifest provenance | C-01 | no | S |
| [C-03](C-03-html-adapter.md) | HTML adapter | C-01 | no | L |
| [C-04](C-04-openapi-adapter.md) | OpenAPI 3.2 adapter | C-01 | no | L |
| [C-05](C-05-errors-json-adapter.md) | `errors.json` adapter | C-01 | no | S |
| [C-06](C-06-overlay-schema-loader.md) | Overlay schema and loader (17 kinds) | C-01 | no | M |
| [C-07](C-07-fill-dsl.md) | Fill-DSL for shortcuts | C-06 | no | M |
| [C-08](C-08-merge-cross-check.md) | Merge and cross-check | C-03, C-04, C-05, C-06 | no | L |
| [C-09](C-09-resolution-passes.md) | Resolution passes: D18, D109, unions | C-08 | no | M |
| [C-10](C-10-ledger-diff.md) | Compat ledger and `diff` | A-11, C-01, C-08 | no | M |
| [C-11](C-11-import-legacy.md) | `import-legacy` (Python, PD-10) + diff mode | C-06, C-07, C-10 | no | M |
| [C-12](C-12-enums-error-reason-emitter.md) | Enums and `ErrorReason` emitter | C-05, C-09, C-11 | no | M |
| [C-13](C-13-reexport-modules.md) | Re-export modules and `__init__` (D16) | C-09 | partial | S |
| [C-14](C-14-pyi-stub-emitter.md) | `.pyi` stub emitter | B-06, B-10, C-09, C-10, C-13 | yes | L |
| [C-15](C-15-bot-methods-emitter.md) | `_BotMethods` mixin emitter | C-09, C-10 | no | M |
| [C-16](C-16-router-observers-update-tables.md) | Router observers and update tables | C-09 | no | S |
| [C-17](C-17-utility-signature-emitter.md) | Builder/utility signature emitter (D59) | C-09 | no | M |
| [C-18](C-18-rust-type-emitter.md) | Rust type emitter (golden diff vs B spike) | B-03, B-04, B-05, B-06, B-07, B-13, B-14, C-09, I-12 | yes | L |
| [C-19](C-19-rust-forward-compat-emitter.md) | Rust forward-compat emitter | B-04, B-13, B-14, C-18 | yes | M |
| [C-20](C-20-rust-methods-shortcuts-emitter.md) | Rust methods, encoder tables, shortcuts, `send_copy` | B-09, B-13, C-07, C-10, C-11, C-18, I-12 | yes | L |
| [C-21](C-21-generated-tests-emitter.md) | Generated-tests emitter | A-04, C-18, C-19, C-20 | yes | M |
| [C-22](C-22-docs-rst-emitter.md) | Docs `.rst` index emitter | C-09 | no | S |
| [C-23](C-23-check-offline-determinism.md) | `check`, offline determinism, CI job | C-10, C-12, C-13, C-15, C-16, C-17, I-05 | no | M |
| [C-24](C-24-scheduled-online-reextract.md) | Scheduled online re-extract job | C-02, C-08, C-11 | no | S |
| [C-25](C-25-historical-scenario-tests.md) | Historical diff + scenario tests (exit gate) | C-08, C-09, C-10, C-11, C-20, C-21, C-23 | partial | M |
| [C-26](C-26-removal-inventory-signature-table.md) | 4.0 removal inventory + 3.x signature table | A-11 | no | S |
| [C-27](C-27-port-ext-helpers.md) | Port remaining hand-written helpers to `*_ext.rs` (PD-16) | B-10, B-13, C-18, D-17 | yes | M |

## Order and parallel lanes

1. **Foundation:** C-01, which needs B-01's workspace skeleton.
2. **Inputs, in parallel:** lane A C-03 (HTML), lane B C-04 (OpenAPI), lane C C-05 + C-02, lane D C-06 → C-07.
3. **IR:** C-08 → C-09, then C-10.
4. **Migration of config:** C-11 (needs C-06/C-07/C-10), then C-26 and C-24.
5. **Python emitters, in parallel after C-09:** C-12, C-13, C-15, C-16, C-17, C-22. Then C-23 turns on the offline gate.
6. **After the B-13 go:** C-18 → (C-19, C-20 in parallel) → C-21; C-14 (needs B-06/B-10); C-27 (needs D-17).
7. **Exit:** C-25.

Cross-story outputs:
- D: ErrorReason (C-12 → D-02), `_BotMethods` (C-15 → D-01), encoder/return/idempotent tables (C-20 → D-07/D-08/D-09, G-13).
- E: observers and update tables (C-16 → E-05/E-09).
- G: utility signatures (C-17 → G-11), lazy display-field marks (C-06/C-20 → G-06).
- H: toolkit tables (C-16 → H-11).
- I: stubs (C-14 → I-04/I-09), docs pages (C-22 → I-09/I-10), raw bundles (C-02 → I-02), signature tables (C-26 → I-15/I-17/I-18; generated on `dev-3.x` and merged forward).

## Open owner questions collected from the plans

Each item is a "Decide … (proposed default)" checklist entry in the named plan:
- snapshot retention, plus the D6b re-confirmation (C-01);
- fixture policy (C-03, C-25);
- overlay file layout (C-06);
- fill-DSL grammar and guard exception (C-07);
- "unchanged entity" and merge precedence (C-08);
- request-only twin fields vs the 4.0 reset, and derived reserved names (C-09);
- the ledger window's version half (C-10);
- old-param translation scope (C-15);
- `event_type` location (C-16);
- utility mixin shape (C-17);
- formatter pin (C-23).
