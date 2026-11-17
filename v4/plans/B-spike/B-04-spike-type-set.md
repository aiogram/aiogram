# B-04 — Spike type set (hand-written in emitted shape)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-00](B-00-freeze-gate-spec.md), [B-03](B-03-decode-runtime.md), [B-14](B-14-unions-envelope-batch-decode.md) |
| Blocks | [B-05](B-05-views-cache-gc-routing-keys.md), [B-09](B-09-sendmessage-encoder-response.md), [C-18](../C-butcher/C-18-rust-type-emitter.md), [C-19](../C-butcher/C-19-rust-forward-compat-emitter.md), [B-13](B-13-gate-run-and-decision.md) |
| Gate-conditional | no |
| Decisions | PD-30, PD-03, D4, D10, D85, D106, D107, D109 |
| Sources | [01-models.md §3.1, §3.6, §5](../../research/01-models.md), [02-butcher.md §3, §5](../../research/02-butcher.md), [10-forward-compatibility.md §3](../../research/10-forward-compatibility.md), [13-aiogram-rust-review.md B1, B18, B20, B21](../../research/13-aiogram-rust-review.md), [19 D107, D109](../../research/19-review-resolutions.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The gate needs real types: a wide `Message`, tagged and undiscriminated unions with `Unknown` variants, collections
and nested objects, decoded from the pinned fixtures. 01 §5.1 says to generate them with a "prototype butcher", but
butcher is milestone C and comes after the gate (D121). Rust emitters built first would be wasted on a no-go (D104).
**PD-30 settles it:** the spike types are **hand-written in exactly the shape the emitter will produce**. They hold
per-type data (field tables) and trait impls, with no per-type logic. C-18 must reproduce them as a golden diff.

## Scope

**In:**
- **Types** (the final list is the closure fixed in B-00). Proposed: `Update`, `Message`, `User`, `Chat`,
  `MessageEntity`, `PhotoSize`, `InlineKeyboardMarkup`, `InlineKeyboardButton`, `CallbackQuery`,
  `InaccessibleMessage`, `MessageOriginUser`, `MessageOriginHiddenUser`, `MessageOriginChat`,
  `MessageOriginChannel`, `LinkPreviewOptions`, `ReplyParameters`.
- **Unions.**
  - `MaybeInaccessibleMessage` (`Message | InaccessibleMessage`): undiscriminated, predicate `date == 0` →
    `InaccessibleMessage` (D85 / D107), with an `UnknownMaybeInaccessibleMessage` for malformed members (D107).
  - `MessageOrigin`, tagged by `type`, with `UnknownMessageOrigin` carrying the common fields `type` and `date`
    plus raw.
- **Files.** Placed where C-18 will emit them: `crates/aiogram-core/src/generated/types/<snake_name>.rs` and
  `src/generated/unions/<snake_name>.rs`. Each file starts with
  `// HAND-WRITTEN SPIKE (PD-30): C-18/C-19 must reproduce this file byte-for-byte or record the diff`.
- **The wide `Message`.**
  - The complete field table, every field of the current Bot API, copied from 3.x
    `.butcher/types/Message/entity.json`. A one-off extraction script may produce it; commit the output, not the
    script.
  - The hot set from the 01 §3.1 overlay list: `message_id, date, chat, from, text, entities, caption, photo,
    reply_markup, message_thread_id, …`. Everything else goes in the sorted cold vec.
- **`Update`.**
  - Every update-type field is in the table. Only `message`, `edited_message` and `callback_query` are typed; the
    others are opaque.
  - `event_type` is generated-shaped from the update fields. An unknown top-level key returns the key itself, and
    `event` returns `UnknownEvent(type, raw)` (10 Layer 1).
- **Enums.** Enum-valued fields (`Chat.type`, `MessageEntity.type`, `MessageOrigin.type`) get Rust enums with
  `Unknown(Box<str>)` and interned strings.
- **Collections.** `entities`, `photo` and keyboard rows are declared as collection fields, exposed as tuples
  (D106) by B-05.
- **Reserved names.** `bot` is reserved (D109): no spike type has a colliding wire field, and a cargo test asserts
  no field table maps to a reserved exact name (`bot`, `raw`, `raw_json`, `to_json`, `to_dict`, `from_json`,
  `from_dict`, `replace`, `as_`, `model_*` aliases).
- **Emitter rules.** B18 trait placement, B20 locals, B21 hoisting; no per-type helper logic. That lives in
  `*_ext.rs` (B-10).

**Out:**
- Python views (B-05) and semantics (B-06).
- `SendMessage` (B-09).
- Every other Bot API type (C-18).
- The overlay and Fill-DSL (C-06 / C-07).
- `send_copy` / content-kind tables beyond what `routing_keys()` needs (C-20, B-05).

## Checklist

- [ ] Take the final type list from `benchmarks/b_gate/gate.toml` (B-00).
- [ ] Decide how out-of-set field types are represented (proposed default: the `Message` / `Update` field tables are
  **complete**, so width and the cold layout are realistic. Fields whose type is outside the spike set use the
  opaque kind: kept as raw, readable only through `.raw`, and their attribute raises
  `NotImplementedError("spike: <Type> not in spike set")`. B-00 guarantees that no gated fixture populates one.
  B-13 lists them). Record in Notes and flag to owner.
- [ ] Hand-write the data structs, field tables and trait impls for each type in the C-18 target paths, with the
  PD-30 header.
- [ ] Write the `Message` field table (one-off extraction allowed), with hot / cold assignment and a comment naming
  the source `entity.json` revision.
- [ ] Write the `MaybeInaccessibleMessage` predicate union and the `MessageOrigin` tagged union with their `Unknown`
  variants.
- [ ] Write `Update.event_type` / `event` / `UnknownEvent` from the update-field table.
- [ ] Add the reserved-name cargo test (D109).
- [ ] Tests: `cargo test` decoding every gated A-04 fixture with no opaque field touched. Unknown `MessageOrigin`
  tag, malformed `MessageOrigin` member, `date == 0` → `InaccessibleMessage`, unknown `Chat.type` value and unknown
  update type all decode.
- [ ] No changelog or registry entry (not wired, PD-03). The `Unknown…` union members are breaking change 9; their
  registry entry belongs to C-19.

## Acceptance criteria

- Every gated A-04 fixture decodes through `cargo test`, and a debug walk checks that the decoded field set equals
  the fixture's key set: unknown keys land as raw ranges, and nothing is silently dropped.
- The unknown-tag, malformed-member, `date == 0`, unknown-enum and unknown-update-type cases decode without error to
  the documented variants.
- Each spike type file contains only data and trait impls. A grep check finds no `fn` bodies other than
  table-driven trait methods; helpers live in `*_ext.rs`.
- `cargo llvm-lines` shows no per-caller generic instances of the decode traits (B18).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| A prototype butcher generating the spike types (01 §5.1) | Butcher is C, after the gate; Rust emitters would be wasted on a no-go | PD-30, D121, D104 |
| Free-form hand-written Rust | The gate must measure the emitted shape, and C-18 needs a golden reference | PD-30 |
| A truncated `Message` (only spike-relevant fields) | Width and cold layout drive memory; the gate needs the real width | 01 §3.1, R04 |
| `ChatMember` as the tagged spike union | 6 variants × ~15 fields of hand-written cost. `MessageOrigin` sits on the message path of the realistic fixture and covers the same `Unknown` mechanism | B-00 type closure |
| Declaration-order fallback for `MaybeInaccessibleMessage` | Dropped | D107 |

## Validation

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
make dev
uv run pytest tests
```

## Workflow notes

- Inputs: the B-03 traits and value kinds, B-14's union dispatch; the B-00 type list; A-04 fixtures; 3.x `.butcher/types/*/entity.json`
  (read-only).
- Outputs: the golden reference files for C-18 (types) and C-19 (unions, `Unknown`, unknown update type), and the
  types that B-05, B-06 and B-09 build on.
- `Message` and the unions can be written in parallel by two people.

## Notes
