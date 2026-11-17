# C-09 — Resolution passes: D18 twins, D109 names, union classification

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-08](C-08-merge-cross-check.md) |
| Blocks | [C-12](C-12-enums-error-reason-emitter.md), [C-13](C-13-reexport-modules.md), [C-14](C-14-pyi-stub-emitter.md), [C-15](C-15-bot-methods-emitter.md), [C-16](C-16-router-observers-update-tables.md), [C-17](C-17-utility-signature-emitter.md), [C-18](C-18-rust-type-emitter.md), [C-22](C-22-docs-rst-emitter.md), [C-25](C-25-historical-scenario-tests.md) |
| Gate-conditional | no |
| Decisions | D18, D109, D92, D85, D107, D10, D118 |
| Sources | [02-butcher.md §3 items 1–3, 6, 7](../../research/02-butcher.md), [19 D107, D109, D118](../../research/19-review-resolutions.md), [01-models.md §3.1, §3.2, §3.6, §3.7](../../research/01-models.md), [10-forward-compatibility.md §3](../../research/10-forward-compatibility.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Several API-shaping rules sit between the merged IR and the emitters:
- the 7 schema-only `Input*` twins are merged into the documented type (D18);
- wire names that collide with reserved Python names are renamed (D109, e.g. `bot` → `bot_user`);
- unions are classified as decoded or request-only, because only decoded unions get `Unknown…` variants (D107);
- every decoded undiscriminated union needs a tag or predicate (D85/D107).

All emitters read the result, so these rules are applied once, here.

## Scope

**In:** `crates/butcher/src/resolve.rs`, producing the emit IR (merged IR plus overlay applied):
- **D18 twin merge.** The list is computed: schema `InputX` where `X` is documented and `InputX` is not. Today that is
  `InputAcceptedGiftTypes`, `InputBotCommand`, `InputChatAdministratorRights`, `InputChatPermissions`,
  `InputLinkPreviewOptions`, `InputMessageEntity`, `InputSwitchInlineQueryChosenChat`. The result is one class with the
  union of fields; a field is required only where both shapes require it; the response-only `const: true` is dropped.
  Direction-specific requiredness and consts stay in the IR (D118). The 67 documented `Input*` types are untouched.
  `check` reports any change to the computed list.
- **D109 names.** Python names (`from` → `from_user`, keyword-safe), overlay renames, and the collision check against
  the reserved set. The check fails on a new collision until `names.toml` has a rename.
- **Union classification.** A union is *decoded* if it is reachable from a response-direction type or an `Update` field;
  otherwise it is request-only (ChatId, DateTime, InputFile, … get no `Unknown`). Each decoded union records its tag or
  overlay predicate. A decoded undiscriminated union without one fails (D85/D107). Common fields of each union's
  variants are computed for `Unknown<Union>` (10 Layer 1).
- **Datetime list.** Fields listed in `datetime.toml` become datetime. An unlisted int field whose description matches
  `Unix time` is a warning.
- **Enum naming** from `enums/*.toml` (`parse`/`multi_parse`/`static`/`extract`), with `ContentType` excluded (11 §1).

**Out:** emitting anything (C-12+), the ledger (C-10).

## Checklist

- [ ] Twin computation and merge, with a unit test per rule (union of fields, both-required, const dropped, direction facts kept).
- [ ] **Decide request-only twin fields vs the 4.0 ledger reset** (02 §3 item 7 says request-only fields such as
  `can_send_media_messages` "go through the ledger", but the ledger is empty at 4.0, D6c). Proposed default: a
  request-only field that the documented type doesn't have is **dropped at 4.0**; this plan appends their
  `removal-4.0` registry entries itself on dev-4.x (C-26 runs on dev-3.x and doesn't see them).
  It is not added to the ledger, since it was never a documented field. Record it in Notes and flag it to the owner.
- [ ] **Decide how the reserved-name set is built** (proposed default: **derived**, not hand-listed. It is the union of
  the base-class surface (`bot`, `raw`, `raw_json`, `to_json`, `to_dict`, `from_json`, `from_dict`, `replace`, `as_`,
  `model_*` aliases including the removed-but-hinting `model_fields`), `decode_error` on `Unknown…` variants,
  `event_type`/`event` on `Update`, every generated shortcut name on that type, and every name in the type's
  `<type>_ext.pyi` fragment. Exact names, not prefixes, so `UniqueGiftColors.model_custom_emoji_id` stays legal).
  Record it in Notes and flag it to the owner.
- [ ] Rename application, plus a check that fails on a new collision.
- [ ] Decoded/request-only union classification and the common-fields computation.
- [ ] Undiscriminated-union rule check (12 today, 3 decoded: `MaybeInaccessibleMessage`, ChatMember results, MenuButton results).
- [ ] Datetime warning; enum naming.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- The computed twin list on the 10.3 schema fixture equals the 7 names above, and a test asserts it.
- `ChatPermissions` is all-optional after the merge (3.x parity), with direction facts still present in the IR.
- A fixture with a new wire field `raw` on some type fails with "collision with reserved name `raw`; add a rename to names.toml".
- `ManagedBotCreated.bot` / `ManagedBotUpdated.bot` resolve to Python `bot_user` (3.x parity).
- `UniqueGiftColors.model_custom_emoji_id` passes the collision check.
- A fixture with a decoded undiscriminated union and no overlay rule fails `build`.
- `ChatId` / `InputFile` unions are classified request-only and get no `Unknown` variant.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Generate the 7 schema-only `Input*` twins as separate classes | Not Bot API types; doubles the surface | D18 |
| Reserved names as prefixes (`model_*`) | Would forbid `model_custom_emoji_id` | D109 |
| Declaration-order fallback for undiscriminated unions | Silent misdecode | D107 |
| `Unknown` variants for every union | Request-only primitive unions are never decoded | D107 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test -p butcher resolve
```

## Workflow notes

- Every emitter reads this pass's output. C-14 and C-18 rely on the common-fields table, C-19 on the union
  classification. This plan writes the dropped-twin registry entries itself (not C-26).

## Notes
