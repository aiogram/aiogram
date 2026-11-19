# C-10 — Compat ledger and `butcher diff`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-01](C-01-crate-xtask-ir-snapshot.md), [C-08](C-08-merge-cross-check.md), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [C-11](C-11-import-legacy.md), [C-14](C-14-pyi-stub-emitter.md), [C-15](C-15-bot-methods-emitter.md), [C-20](C-20-rust-methods-shortcuts-emitter.md), [C-23](C-23-check-offline-determinism.md), [C-25](C-25-historical-scenario-tests.md) |
| Gate-conditional | no |
| Decisions | D6c, D71, D72, D100, R28, PD-13, PD-24 |
| Sources | [02-butcher.md §4](../../research/02-butcher.md), [16-support-policy.md](../../research/16-support-policy.md), [19 §2 R28](../../research/19-review-resolutions.md), [plans README PD-13](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Legacy butcher keeps backward-compatibility state inside `entity.json`. It re-appends vanished fields as deprecated and
never deletes removed entities; 38 entity files carry such markers today. Neither input source holds this state, so 4.0
keeps it as an explicit committed ledger, `butcher/ledger.toml`.
- **4.0 reset:** the ledger starts **empty**. Everything deprecated during 3.x is dropped (C-26 lists it).
- **Rolling window after 4.0:** a removed item stays deprecated until both 12 months and 2 Bot API "major" versions
  have passed, then it is dropped in an aiogram minor (D6c).
- `keep_position` is gone (D100).

## Scope

**In:**
- `crates/butcher/src/ledger.rs`: `ledger.toml` with `[[removed_field]]` (`entity`, `field`, `removed_in`, `removed_on`,
  `replacement?`) and `[[removed_entity]]` (`entity`, `removed_in`, `removed_on`). No `keep_position`.
- `cargo xtask butcher diff <old-snapshot> <new-snapshot>` writes:
  - a structured change list (added, removed and changed entities, fields, params, enum members, union members);
  - new ledger entries for removals;
  - a `CHANGES/<id>.misc.rst` draft and a PR body draft;
  - `ErrorReason` renames (PD-24), reported as changes.
- Ledger injection into the emit IR: a removed field or entity is re-added, marked `deprecated {removed_in, removed_on,
  replacement}`, so emitters produce `AiogramApiDeprecationWarning` (D72 subclass) at runtime and a `.. deprecated::`
  stub note.
- Due computation in `check`: an entry is due when **both** conditions hold. Due entries are listed. Dropping one is an
  explicit PR that deletes the entry and adds a generated `CHANGES/*.removal.rst` (R28: no implicit drop).
- Registry hand-off: each ledger entry yields a `kind = "api-ledger"` record for `aiogram/_migration/registry.toml`
  (PD-13, schema from A-11). This task writes the generator; I-12 owns the registry CI.

**Out:** the 4.0 reset inventory (C-26); emitting warnings (C-14, C-20); old-param translation (C-15).

## Checklist

- [ ] Ledger schema + loader (`deny_unknown_fields`), and a validation that every entry references an entity or field present in some earlier snapshot.
- [ ] `diff` change list, ledger entry writer, CHANGES and PR-body drafts.
- [ ] Ledger → emit-IR injection with deprecation metadata.
- [ ] **Decide the window's version half** (README D6 / 02 §4 say "2 Bot API **major** versions". Bot API majors have
  shipped roughly yearly, 7.0 Dec 2023 → 8.0 Nov 2024 → 9.0 Apr 2025, so "major" would make the version condition
  dominate the 12 months). Proposed default: count **2 Bot API version bumps of any kind (X.Y)** after `removed_in`.
  The time half is stored as `removed_on`. The version half is evaluated by `check` against the snapshots present, not
  precomputed as a `drop_after` value, because future versions are unknown at diff time. Record it in Notes and flag it
  to the owner.
- [ ] `check` due-list output, and the generated `removal` fragment for a drop PR.
- [ ] `api-ledger` registry record generator (registry schema from A-11).
- [ ] Changelog fragment / migration-registry entry when user-visible: `api-ledger` records are generated per entry. Verify A-11's seed contains the 4.0 ledger-reset entry (`removal-4.0`, breaking change 8).
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- `diff` between two fixture snapshots where a field disappears writes exactly one `removed_field` entry, one changelog line and one registry record.
- The emitted stub and Rust for a fixture ledger entry carry the deprecation (checked in C-14/C-20 tests; here, the injected IR node has `deprecated` set).
- `check` lists an entry as due only when both the 12 months (relative to a fixed test clock) and the version count are met (4-case truth-table test).
- The ledger file on dev-4.x after this task is empty except for a header comment (4.0 reset).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Carry the 3.x deprecated fields into 4.0 | 4.0 reset; explicit exception to D71 | D6c, R28 |
| `keep_position` entries | All generated signatures keyword-only | D100, PD-02 |
| Automatic drop when due | CI must require an explicit due-removal decision | R28 |
| Plain `DeprecationWarning` | Visible subclass | D72 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test -p butcher ledger
cargo xtask butcher diff butcher/snapshots/<a> butcher/snapshots/<b>   # fixture snapshots
```

## Workflow notes

- A-11 defines `registry.toml`'s schema. Its generated writers are 3x-23 (`api-ledger`, AG48xx), C-09 (dropped
  twin fields) and this task, and I-12 owns validation and the Deprecations page.
- C-25 replays historical removals through `diff`.

## Notes
