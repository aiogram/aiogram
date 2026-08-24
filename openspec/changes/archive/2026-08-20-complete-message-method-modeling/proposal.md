## Why

The message surface is the reason the toolkit exists, and it is only half modeled. A bot
that sends an invoice, a game, paid media, a checklist or a rich message gets a
synthesized `Message` that is never stored, so the chat looks empty, `env.calls` is the
only assertion available, and — worse — `actor.click()` cannot find the inline keyboard
that message carried. The same hole exists on the edit side: `EditMessageText`,
`EditMessageCaption` and `EditMessageReplyMarkup` mutate stored messages, but
`EditMessageMedia`, `EditMessageLiveLocation` and `EditMessageChecklist` do not, so a
handler that edits media leaves the world showing the pre-edit content.

None of this needs new world state. Every method here is already the shape of an existing
handler — `handle_send` for the send family, `_edit_target` + `update_message` for the
edit family — and simply was never registered. This is the highest payoff per line of
implementation in the whole remaining API surface.

## What Changes

- **Send family joins the modeled path**: `SendInvoice`, `SendGame`, `SendPaidMedia`,
  `SendChecklist`, `SendLivePhoto` and `SendRichMessage` each append a real `Message` to
  the chat carrying their payload field (`invoice`, `game`, `paid_media`, `checklist`,
  `location`, the rich-message field), with a real `message_id`, reply resolution, topic
  threading and business attribution exactly as `SendMessage` already gets.
- **Edit family is completed**: `EditMessageMedia`, `EditMessageLiveLocation` and
  `EditMessageChecklist` mutate the stored message in place; `StopMessageLiveLocation`
  returns the stored message instead of synthesized noise. All four fail with
  `TelegramBadRequest` on an unknown or deleted target, as the existing edit methods do.
- **Batch methods loop over the modeled singles**: `ForwardMessages` and `CopyMessages`
  produce real forwarded/copied messages in the target chat and return ids that exist.
- **`UnpinAllChatMessages`** clears the `pinned_message_ids` list that `PinChatMessage`
  and `UnpinChatMessage` already maintain, closing the pinning trio.
- **Seeded results where a modeled world is overkill**: `SendChatAction` validates the
  chat and returns `True`; `CreateInvoiceLink` returns a deterministic link;
  `GetFile` echoes the requested `file_id`; `GetUserPersonalChatMessages` reads from the
  user's private chat when one exists.
- `SendRichMessageDraft` and the ephemeral-message methods stay on the record-only path
  by design — a 30-second preview is never persisted by Telegram either.

No breaking changes. Tests that assert only on `env.calls` keep passing; tests gain the
ability to assert on chat state for these methods.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: the modeled method set grows to cover the remaining
  message-producing and message-mutating methods, batch forward/copy, and
  `unpinAllChatMessages`, and the requirement naming the modeled minimum is updated
  accordingly.

## Impact

- **Code**: `aiogram/test/modeling.py` almost exclusively — new registrations plus a small
  `InputMedia`/`InputChecklist` → `Message` field mapping. `world.py` gains no new entity;
  `ChatState.pinned_message_ids` and `update_message` already exist.
- **Tests**: new cases under `tests/test_testing/`, holding the package at 100%.
- **Docs**: the modeled-method list in `docs/dispatcher/testing.rst` is extended.
- **Changelog**: `CHANGES/<issue-or-pr>.feature.rst`.
- **Compatibility**: no new dependencies; Python 3.10–3.14 and PyPy 3.11 as before.
- **Risk**: low. Every method here reuses a handler already proven by the existing suite;
  the only new logic is the input-media field mapping, which is data, not behavior.
