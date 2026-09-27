## Context

Seven methods, one registry keyed by set name. The shape is the same as the invite-link
cluster: correlation is the value, not storage. `getStickerSet` exists so a bot can look
before it writes, and today it returns something unrelated to what the bot built.

Unlike the other clusters in this plan, nothing else in the world reads sticker sets — no
message references one, no membership depends on one. That makes it the safest to add and
the easiest to defer, which is why it is proposed as a candidate rather than a
recommendation.

## Goals / Non-Goals

**Goals:**

- `create → add → get` returns what was built.
- The mistakes a pack bot makes — a taken name, a missing set, a sticker that is not there —
  fail as they would in production.

**Non-Goals:**

- **Sticker image data.** A sticker is a `Sticker` object with a file id; no bytes exist,
  no dimensions are derived, no thumbnails are produced. This holds even alongside
  `fail-loudly-on-unmodeled-downloads`: sticker files are not registered as downloadable
  content, because a pack bot does not download them.
- The per-sticker attribute setters. Emoji lists, keywords, mask positions and ordering are
  written and never read; modeling them would be storage with no reader.
- Telegram's pack rules: the 120-sticker limit, format compatibility between a set's
  stickers, the `<name>_by_<bot_username>` naming convention. Policy.
- Custom emoji set semantics beyond the shared registry.

## Decisions

### D1. Keyed by name, because Telegram is

`World.sticker_sets: dict[str, StickerSetState]`. Every method in the cluster takes
`name`, which makes the registry a direct lookup and the "name already taken" error a
membership test rather than a scan.

### D2. Stickers are stored as `Sticker` objects, not a second state class

`StickerSetState.stickers: list[Sticker]` holds the generated API type directly, unlike
messages, which are stored as `Message` but *rebuilt* on edit. Stickers have no editable
state in this cluster — add, remove and reorder are list operations — so a parallel
`StickerState` would be a wrapper with no fields of its own.

*Consequence:* if the attribute setters are ever modeled, this decision is the thing to
revisit, because mutating a frozen `Sticker` in a list is exactly the friction
`update_message` exists to handle.

### D3. `replaceStickerInSet` is delete-then-add at the same position

Rather than a distinct operation. Telegram documents it as equivalent, and expressing it in
terms of the other two keeps the position handling in one place.

### D4. Uploads return a stable id and register nothing

`uploadStickerFile` mints a file id from the world counter and stores no content — a
deliberate contrast with `fail-loudly-on-unmodeled-downloads`, where uploaded *document*
bytes are registered. The difference is that a bot uploads a document to send it and often
reads it back, while it uploads a sticker to put it in a pack and never downloads it. If
that assumption turns out wrong, the fix is to route sticker uploads through the same file
registry.

## Risks / Trade-offs

- **Low demand** → effort spent on a cluster nobody exercises. Mitigated by proposing it as
  a candidate: it should be built when someone asks, and this document exists so that when
  they do, the decision is already made.
- **Storing generated `Sticker` objects directly (D2)** → awkward if attributes become
  mutable later. Recorded above as the thing to revisit rather than pre-solved.
- **Partial cluster is worse than none** → modeling `getStickerSet` alone would return a
  real-looking set that no write ever reaches. Mitigated by shipping the seven together.
- **Someone expects sticker files to download** → mitigated by the non-goal and by
  `fail-loudly-on-unmodeled-downloads` raising a message that names how to register content.

## Migration Plan

Purely additive. A test asserting on a synthesized `getStickerSet` result would newly see an
empty or missing set — which is the defect being fixed.

## Open Questions

- Should the 120-sticker limit be enforced, given that "is my pack full?" is the branch this
  cluster exists to make testable? Tempting, but it is policy, and a test wanting that
  branch can declare a set already at the limit. Leaning no; revisit if declaring 120
  stickers proves annoying enough that people ask.
