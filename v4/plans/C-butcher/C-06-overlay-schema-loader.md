# C-06 — Overlay schema and loader

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-01](C-01-crate-xtask-ir-snapshot.md) |
| Blocks | [C-07](C-07-fill-dsl.md), [C-08](C-08-merge-cross-check.md), [C-11](C-11-import-legacy.md), [G-06](../G-features/G-06-lazy-text-capture.md), [G-13](../G-features/G-13-retry-middleware.md) |
| Gate-conditional | no |
| Decisions | D11, D47, D83, D85/D107, D109, R19, R24, PD-24, PD-25 |
| Sources | [02-butcher.md §3, §5.1](../../research/02-butcher.md), [01-models.md §3.1, §3.6](../../research/01-models.md), [06-utils.md §3](../../research/06-utils.md), [05-network.md §2.5 D43](../../research/05-network.md), [14-testing.md §3](../../research/14-testing.md), [03-routing.md §3](../../research/03-routing.md), [codex-review.md R24](../../research/codex-review.md), [plans README PD-24, PD-25](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The legacy YAML overlays have no schema. `tagged: true` in `.butcher/types/MaybeInaccessibleMessage/subtypes.yml` is
dead config nobody noticed. The 4.0 overlay is strict: unknown keys are errors, and every reference is checked against
the IR (02 §3). R24 found that 02 §3 omits overlay data that later features need. This plan defines the **complete
inventory**.

## Scope

**In:** `crates/butcher/src/overlay.rs`, loading `butcher/overlay/**/*.toml` with `deny_unknown_fields` and checking
references against the IR. Kinds:

| # | Kind | File | Consumer |
|---|---|---|---|
| 1 | Python names, aliases (`from` → `from_user`), keyword-safe names, collision renames (`bot` → `bot_user` on `ManagedBotCreated`/`ManagedBotUpdated`, D109) | `names.toml` | C-09, emitters |
| 2 | Named enums for inline enum/const sets, aiogram-only enums (`UpdateType`), the `extract` rule (enum from field names), `parse`/`multi_parse` rules | `enums/<Name>.toml` | C-09, C-12 |
| 3 | Datetime fields: an explicit list | `datetime.toml` | C-09, C-18 |
| 4 | Bot-level `Default(...)` per parameter | `defaults.toml` | C-14, C-15, C-20 |
| 5 | Shortcuts: target method + fill-DSL text, `ignore`, guards, `handwritten = true` | `shortcuts/<Type>.toml` | C-07, C-20 |
| 6 | Undiscriminated union decode strategy: tag or predicate (no declaration-order fallback, D107) | `unions.toml` | C-09, C-19 |
| 7 | `Input*` twin merge overrides (the list itself is computed, D18) | `twins.toml` | C-09 |
| 8 | Hot fields for the sparse layout (01 §3.1) | `layout.toml` | C-18 |
| 9 | Heuristic overrides for html-only releases (returns, consts, subtypes, enum members), including the 3 legacy `returning` overrides | `heuristics.toml` | C-08 |
| 10 | Docs extras | `docs.toml` | C-14, C-22 |
| 11 | `idempotent` per method: **explicit decision for every method**. Missing means non-idempotent plus a `check` error (PD-25) | `methods.toml` | C-20, G-13 |
| 12 | Lazy display fields (`text`, `caption`, `title`, button `text`, …) that accept lazy text (06 §3) | `display.toml` | C-14, C-18, C-20, G-06 |
| 13 | `send_copy` content map: content kind → method + field map; a new content kind without a mapping fails `check` | `content.toml` | C-20, C-16 |
| 14 | Routing content kinds for `routing_keys()` (03 §3, B14) | `content.toml` | C-19 (Rust table), C-16 (Python table) |
| 15 | Event-context paths per update type (`user`, `chat`, `thread_id`, `business_connection_id`), replacing hand-written `UserContextMiddleware.resolve_event_context` (`aiogram/dispatcher/middlewares/user_context.py`) | `events.toml` | C-16 |
| 16 | Secondary bases (D83; replaces the 18 `bases` entries of `replace.yml`; `MutableTelegramObject` is not allowed, D15) | `bases.toml` | C-14, C-18 |
| 17 | `ErrorReason` member-name pins (PD-24) and stable overrides (`MESSAGE_NOT_MODIFIED`, `BOT_BLOCKED`) | `errors.toml` | C-12 |

- No testing-toolkit "fake model / synthesise" marks: fake coverage is enforced by H-11's pytest guard instead.
- Validation errors name the file, the key path and the IR entity that doesn't exist.
- An overlay digest (sha256 over the sorted file contents) is written to the manifest (C-01/C-02).

**Out:** the fill-DSL grammar (C-07; this task stores the DSL text unparsed); applying the overlay (C-08, C-09);
importing the legacy YAML (C-11).

## Checklist

- [ ] Serde structs for kinds 1–17, all with `deny_unknown_fields`.
- [ ] Reference checker against the IR (entity, field, method, param, enum, union, update type).
- [ ] Overlay digest for the manifest.
- [ ] One fixture per kind: a valid file, an unknown key, a dangling reference.
- [ ] Document each kind in `butcher/overlay/README.md` (one short paragraph each, with an example).
- [ ] **Decide the file layout** (proposed default: one file per kind as in the table, with `shortcuts/` and `enums/`
  split per entity so Bot API bump diffs stay reviewable). Record it in Notes and flag it to the owner.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- A key misspelt in any kind fails with `file:key.path: unknown field`.
- A reference to a non-existent entity or field fails with the name and the closest IR match.
- The equivalent of the dead `tagged: true` key in `MaybeInaccessibleMessage/subtypes.yml` is rejected.
- The overlay digest changes when any overlay byte changes and is stable otherwise.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Inline Python `fill` expressions (legacy) | Not declarative, not checkable; replaced by the fill-DSL | 02 §3, D11 |
| Declaration-order fallback for undiscriminated unions | Silent misdecode | D107 |
| `get*`-prefix rule for idempotency | Not a safety property; explicit metadata | R19, PD-25 |
| `MutableTelegramObject` as a base | All types immutable | D15 |
| Testing-toolkit `fake = "modelled" \| "synthesize"` marks in the overlay (14 §3) | Butcher can't see the Python fake registry; H-11's pytest guard gives the same coverage check | H-11 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test -p butcher overlay
```

## Workflow notes

- C-11 writes the initial overlay files in this schema. Kinds 11–17 have no legacy source and are authored by hand in
  C-11's follow-up checklist or by the consuming plans (E-09, G-06).
- Kinds 11, 12, 13 and 15 must be filled before C-23 can turn on the corresponding `check` rules.

## Notes
