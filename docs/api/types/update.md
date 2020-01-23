# Update

## Description

This object represents an incoming update.

At most one of the optional parameters can be present in any given update.


## Attributes

| Name | Type | Description |
| - | - | - |
| `update_id` | `#!python int` | The update‘s unique identifier. Update identifiers start from a certain positive number and increase sequentially. This ID becomes especially handy if you’re using Webhooks, since it allows you to ignore repeated updates or to restore the correct update sequence, should they get out of order. If there are no new updates for at least a week, then identifier of the next update will be chosen randomly instead of sequentially. |
| `message` | `#!python Optional[Message]` | Optional. New incoming message of any kind — text, photo, sticker, etc. |
| `edited_message` | `#!python Optional[Message]` | Optional. New version of a message that is known to the bot and was edited |
| `channel_post` | `#!python Optional[Message]` | Optional. New incoming channel post of any kind — text, photo, sticker, etc. |
| `edited_channel_post` | `#!python Optional[Message]` | Optional. New version of a channel post that is known to the bot and was edited |
| `inline_query` | `#!python Optional[InlineQuery]` | Optional. New incoming inline query |
| `chosen_inline_result` | `#!python Optional[ChosenInlineResult]` | Optional. The result of an inline query that was chosen by a user and sent to their chat partner. Please see our documentation on the feedback collecting for details on how to enable these updates for your bot. |
| `callback_query` | `#!python Optional[CallbackQuery]` | Optional. New incoming callback query |
| `shipping_query` | `#!python Optional[ShippingQuery]` | Optional. New incoming shipping query. Only for invoices with flexible price |
| `pre_checkout_query` | `#!python Optional[PreCheckoutQuery]` | Optional. New incoming pre-checkout query. Contains full information about checkout |
| `poll` | `#!python Optional[Poll]` | Optional. New poll state. Bots receive only updates about stopped polls and polls, which are sent by the bot |
| `poll_answer` | `#!python Optional[PollAnswer]` | Optional. A user changed their answer in a non-anonymous poll. Bots receive new votes only in polls that were sent by the bot itself. |



## Location

- `from aiogram.types import Update`
- `from aiogram.api.types import Update`
- `from aiogram.api.types.update import Update`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#update)
- [aiogram.types.CallbackQuery](../types/callback_query.md)
- [aiogram.types.ChosenInlineResult](../types/chosen_inline_result.md)
- [aiogram.types.InlineQuery](../types/inline_query.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.Poll](../types/poll.md)
- [aiogram.types.PollAnswer](../types/poll_answer.md)
- [aiogram.types.PreCheckoutQuery](../types/pre_checkout_query.md)
- [aiogram.types.ShippingQuery](../types/shipping_query.md)
