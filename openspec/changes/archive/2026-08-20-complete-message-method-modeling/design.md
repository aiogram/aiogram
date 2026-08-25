## Context

`aiogram/test/modeling.py` already contains everything this change needs:

- `handle_send` (`@models(SendMessage, *MEDIA_FIELDS)`) builds a `Message` through
  `build_message`, which resolves the chat, allocates a per-chat `message_id`, applies
  topic threading and business sender attribution, and appends to `ChatState.messages`.
  `MEDIA_FIELDS` is a plain `dict[type[TelegramMethod], str]` mapping a method type to the
  `Message` field its payload lands in.
- `_edit_target` resolves `(chat, message_id)` from an edit method and raises
  `TelegramBadRequest` when the target is missing, and `ChatState.update_message` mutates
  a stored message in place.
- `ForwardMessage` and `CopyMessage` handlers exist and already do the origin/attribution
  work their batch forms need.
- `ChatState.pinned_message_ids` is maintained by the pin handlers.

So the work is overwhelmingly registration and data, not new machinery. The one genuinely
new piece is mapping an `InputMedia*` input object onto the `Message` field it becomes.

## Goals / Non-Goals

**Goals:**

- Every method that produces a message stores one, so chat-state assertions and
  `actor.click()` work uniformly across the send surface.
- Every method that mutates a message mutates the stored one, so the world never shows
  pre-edit content after a successful edit.
- Reuse the existing handlers rather than growing parallel implementations.

**Non-Goals:**

- Media processing. An `InputMediaPhoto` becomes a `PhotoSize` with a plausible
  `file_id`; no bytes are read, no dimensions are derived, no thumbnails are produced.
- Payment, game or checklist *semantics*. `sendInvoice` stores an `Invoice` on the
  message; it does not create an order, a balance or a payment flow. That flow belongs to
  `complete-actor-triggers`.
- Ephemeral messages (`sendMessageDraft`, `sendRichMessageDraft`, the
  `editEphemeralMessage*` family, `deleteEphemeralMessage`). Telegram does not persist
  them either; they stay record-only.

## Decisions

### D1. Extend `MEDIA_FIELDS` rather than write new handlers

`SendGame`, `SendPaidMedia`, `SendChecklist`, `SendLivePhoto`, `SendInvoice` and
`SendRichMessage` are all "append a `Message` carrying one payload field". They join
`MEDIA_FIELDS` (`SendGame: "game"`, `SendInvoice: "invoice"`, …) and inherit
`handle_send` unchanged, which means they inherit reply resolution, topic threading,
business attribution and default resolution for free — and stay correct if any of those
change later.

`SendLivePhoto` maps to `Message.live_photo` and `SendRichMessage` to
`Message.rich_message` — both fields already exist on the generated `Message`, so neither
needs an approximation.

*Alternative rejected:* a handler per method. Six near-identical functions that would
drift apart the first time `build_message` grows a parameter.

### D2. Derive the message field from the input media's own name

`EditMessageMedia` receives an `InputMedia*` union member; the stored message needs a
`PhotoSize`/`Video`/`Document`/… instead. Every member of the method's media union is
named `InputMedia<Field>` and maps to the snake-cased `Message` field of the same stem
(`InputMediaLivePhoto` → `live_photo`), so the mapping is *derived* rather than
hand-maintained, and a future member works without touching this package. The value itself
comes from the existing `synthesize` machinery, as it already does on the send path.

The parametrized guard test over every union member is what keeps the derivation honest:
a member whose name does not map fails aiogram's own CI with the member named. This is the
same bargain the outbound synthesis guard already makes — derive from generated metadata,
and let a test catch the shape that breaks the rule.

`EditMessageChecklist` needs no mapping at all; it writes `checklist` directly.

### D7. A sent payload carries the values the request actually had

`build_message` synthesized the whole media payload, so `sendLocation(latitude=48.85, …)`
stored a `Location` with synthesized coordinates — the world showed something the bot never
did. Surfaced while implementing D2: the new `editMessageLiveLocation` writes real
coordinates, so send and edit disagreed.

After synthesizing the payload, any field the *request* carries under the same name
overwrites it, guarded by `annotation_accepts` so a request field that merely shares a name
with a differently-typed payload field (`sendVideo.cover`, a file id, against `Video.cover`,
a `PhotoSize`) is left alone. Derived, so it covers the whole send family at once:
location, venue, contact, dice, video/audio/voice durations and dimensions, paid-media star
count.

Media *content* stays synthesized — no bytes are read, and a `file_id` remains plausible
rather than echoed. Only scalars the request stated are carried.

*Scope note:* this corrects methods that shipped in earlier changes, and was taken
deliberately rather than deferred, because leaving it would have made this change's own
edit semantics disagree with its send semantics.

### D3. Batch methods delegate to the single-message handlers

`ForwardMessages`/`CopyMessages` iterate their `message_ids`, call the existing single
handler per id, and collect the results. Telegram skips messages it cannot copy rather
than failing the batch; the fake matches that for individually-missing ids and raises only
when the *source chat* is unknown — the one error a test would deliberately provoke.

*Trade-off accepted:* per-message skipping means a batch can silently return fewer ids
than requested. That is what Telegram does, and the returned list makes it observable.

### D8. Forwarding records where the message came from

`handle_forward` stored no `forward_origin`, so a forwarded message and a copied one were
indistinguishable in the world — and this change's own spec distinguishes them. Since the
batch form delegates to the single form (D3), the fix belongs in the shared path, where
both callers get it.

A forward from a channel records `MessageOriginChannel`; anything else records
`MessageOriginUser` from the stored sender. The hidden-user and sender-chat origins are
*not* implemented: nothing in the world can produce an anonymous sender yet, so they would
be dead branches. They arrive with the change that adds channel posts and anonymous
admins.

Copies explicitly clear `forward_origin`, which is the whole observable difference between
the two operations.

### D4. `stopMessageLiveLocation` returns the stored message, unmodified

Telegram's real behavior — ending the live period — has no observable consequence in a
fake with no clock-driven expiry. Returning the stored message rather than synthesized
noise is the useful half; claiming to model live-period expiry would be fidelity the fake
cannot keep. The `live_period` field is cleared so a test can at least distinguish stopped
from running.

### D5. Seeded results stay seeded, not modeled

`sendChatAction`, `getFile`, `createInvoiceLink` and `getUserPersonalChatMessages` get a
world-derived answer but no state. The line is drawn at "is there something to mutate":
a chat action has no persistence in Telegram either, and a file registry would be a world
entity serving exactly one getter. `getFile` echoing the passed `file_id` is what makes a
download-path test correlate at all, and costs one line.

## Risks / Trade-offs

- **The input-media mapping is derived from names (D2)** → a future `InputMedia` variant
  whose name does not match its `Message` field would not map. Mitigation: a parametrized
  test over every union member asserting the mapping resolves, and an explicit failure
  naming the variant rather than a silently wrong field.
- **Carrying request values matches by name (D7)** → a future request field could share a
  name with a payload field of a compatible type but different meaning. Mitigation: the
  `annotation_accepts` guard rules out the type-mismatched cases, and the send suite
  asserts the carried values per method family.
- **Batch skipping is silent (D3)** → a test could believe three messages were copied when
  two were. Mitigation: the returned identifier list is the assertion surface, and the
  scenario covering it is in the spec.
- **Growing the modeled set is a growing fidelity claim** → each newly modeled method is
  now expected to behave. Mitigation: everything added here reuses handlers the existing
  suite already exercises, so the marginal risk is confined to the payload field mapping.
- **`sendInvoice` may read as "payments are modeled"** → they are not. Mitigation: the
  proposal and the docs section say so explicitly, and the payment flow is scoped to
  `complete-actor-triggers`.

## Migration Plan

Purely additive. A test that today asserts a synthesized return value from one of these
methods keeps passing, because the stored message satisfies the same type. Tests that
assert the chat is *empty* after such a call would newly fail — that is the defect being
fixed, and the changelog calls it out.

## Open Questions

- Should `sendPaidMedia` model the star cost at all, or is storing the `paid_media` field
  enough? Leaning enough: there is no star ledger, and adding one for a single field is
  the cluster this plan explicitly defers.
