## Why

Bot API 10.3 replaced the deprecated `receiver_user_id` / `callback_query_id` send
parameters with a single `ephemeral_message_parameters` object. The `.butcher`
alias config builds that object with an inline conditional expression, which
`butcher` splices verbatim into all 19 `Message.reply_*` shortcuts. Three problems
follow:

1. The construction rule lives in 19 copies of generated code instead of one named
   method, unlike its neighbour `reply_parameters`, which delegates to the
   hand-written `Message.as_reply_parameters()`.
2. Only `receiver_user_id` is ever set. `callback_query_id` and
   `replace_callback_query_message` have no supported way in, short of hand-building
   `EphemeralMessageParameters` and calling `answer()` instead of `reply()`.
3. The fill is applied to all 19 shortcuts, but only 14 send methods declare the
   field. On the other 6 it lands in pydantic's `model_extra` and is serialized into
   the request. This predates 10.3 — the old `receiver_user_id` fill leaked the same
   way.

## What Changes

- Add `Message.as_ephemeral_message_parameters()`, a hand-written helper mirroring
  `Message.as_reply_parameters()`. It returns `EphemeralMessageParameters | None`
  and accepts `callback_query_id` and `replace_callback_query_message` as optional
  keyword arguments.
- Change the `reply` fill in `.butcher/types/Message/aliases.yml` to call that
  helper, replacing the inline conditional.
- Stop applying the fill to the six shortcuts whose target method has no
  `ephemeral_message_parameters` field: `reply_dice`, `reply_poll`, `reply_game`,
  `reply_invoice`, `reply_media_group`, `reply_paid_media`.
- Keep the existing `self.from_user.id` semantics. This is deliberate and out of
  scope here; see design.md.

Not breaking: the generated `reply_*` signatures are unchanged, and the produced
`EphemeralMessageParameters` is identical for the 14 shortcuts that keep the fill.
The six that lose it stop sending a parameter their method never accepted.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-api-codegen`: the "Object shortcuts" requirement gains rules for how a
  shortcut fill is constructed (named helper over inline expression) and a
  constraint that a fill is only applied to shortcuts whose target method declares
  the field.

## Impact

- `.butcher/types/Message/aliases.yml` — generator input, source of truth.
- `aiogram/types/message.py` — the hand-written helper, plus 19 regenerated
  shortcut bodies.
- `tests/test_api/test_types/test_message.py` — existing ephemeral reply tests, plus
  new coverage for the helper and for the six excluded shortcuts.
- `CHANGES/<pr>.bugfix.rst` — the leak onto the six methods is user-visible.
- No change to `aiogram/methods`, `aiogram/enums`, or the dispatcher.
