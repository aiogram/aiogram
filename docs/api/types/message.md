# Message

## Description

This object represents a message.


## Attributes

| Name | Type | Description |
| - | - | - |
| `message_id` | `#!python int` | Unique message identifier inside this chat |
| `date` | `#!python datetime.datetime` | Date the message was sent in Unix time |
| `chat` | `#!python Chat` | Conversation the message belongs to |
| `from_user` | `#!python Optional[User]` | Optional. Sender, empty for messages sent to channels |
| `forward_from` | `#!python Optional[User]` | Optional. For forwarded messages, sender of the original message |
| `forward_from_chat` | `#!python Optional[Chat]` | Optional. For messages forwarded from channels, information about the original channel |
| `forward_from_message_id` | `#!python Optional[int]` | Optional. For messages forwarded from channels, identifier of the original message in the channel |
| `forward_signature` | `#!python Optional[str]` | Optional. For messages forwarded from channels, signature of the post author if present |
| `forward_sender_name` | `#!python Optional[str]` | Optional. Sender's name for messages forwarded from users who disallow adding a link to their account in forwarded messages |
| `forward_date` | `#!python Optional[int]` | Optional. For forwarded messages, date the original message was sent in Unix time |
| `reply_to_message` | `#!python Optional[Message]` | Optional. For replies, the original message. Note that the Message object in this field will not contain further reply_to_message fields even if it itself is a reply. |
| `edit_date` | `#!python Optional[int]` | Optional. Date the message was last edited in Unix time |
| `media_group_id` | `#!python Optional[str]` | Optional. The unique identifier of a media message group this message belongs to |
| `author_signature` | `#!python Optional[str]` | Optional. Signature of the post author for messages in channels |
| `text` | `#!python Optional[str]` | Optional. For text messages, the actual UTF-8 text of the message, 0-4096 characters. |
| `entities` | `#!python Optional[List[MessageEntity]]` | Optional. For text messages, special entities like usernames, URLs, bot commands, etc. that appear in the text |
| `caption_entities` | `#!python Optional[List[MessageEntity]]` | Optional. For messages with a caption, special entities like usernames, URLs, bot commands, etc. that appear in the caption |
| `audio` | `#!python Optional[Audio]` | Optional. Message is an audio file, information about the file |
| `document` | `#!python Optional[Document]` | Optional. Message is a general file, information about the file |
| `animation` | `#!python Optional[Animation]` | Optional. Message is an animation, information about the animation. For backward compatibility, when this field is set, the document field will also be set |
| `game` | `#!python Optional[Game]` | Optional. Message is a game, information about the game. |
| `photo` | `#!python Optional[List[PhotoSize]]` | Optional. Message is a photo, available sizes of the photo |
| `sticker` | `#!python Optional[Sticker]` | Optional. Message is a sticker, information about the sticker |
| `video` | `#!python Optional[Video]` | Optional. Message is a video, information about the video |
| `voice` | `#!python Optional[Voice]` | Optional. Message is a voice message, information about the file |
| `video_note` | `#!python Optional[VideoNote]` | Optional. Message is a video note, information about the video message |
| `caption` | `#!python Optional[str]` | Optional. Caption for the animation, audio, document, photo, video or voice, 0-1024 characters |
| `contact` | `#!python Optional[Contact]` | Optional. Message is a shared contact, information about the contact |
| `location` | `#!python Optional[Location]` | Optional. Message is a shared location, information about the location |
| `venue` | `#!python Optional[Venue]` | Optional. Message is a venue, information about the venue |
| `poll` | `#!python Optional[Poll]` | Optional. Message is a native poll, information about the poll |
| `new_chat_members` | `#!python Optional[List[User]]` | Optional. New members that were added to the group or supergroup and information about them (the bot itself may be one of these members) |
| `left_chat_member` | `#!python Optional[User]` | Optional. A member was removed from the group, information about them (this member may be the bot itself) |
| `new_chat_title` | `#!python Optional[str]` | Optional. A chat title was changed to this value |
| `new_chat_photo` | `#!python Optional[List[PhotoSize]]` | Optional. A chat photo was change to this value |
| `delete_chat_photo` | `#!python Optional[bool]` | Optional. Service message: the chat photo was deleted |
| `group_chat_created` | `#!python Optional[bool]` | Optional. Service message: the group has been created |
| `supergroup_chat_created` | `#!python Optional[bool]` | Optional. Service message: the supergroup has been created. This field can‘t be received in a message coming through updates, because bot can’t be a member of a supergroup when it is created. It can only be found in reply_to_message if someone replies to a very first message in a directly created supergroup. |
| `channel_chat_created` | `#!python Optional[bool]` | Optional. Service message: the channel has been created. This field can‘t be received in a message coming through updates, because bot can’t be a member of a channel when it is created. It can only be found in reply_to_message if someone replies to a very first message in a channel. |
| `migrate_to_chat_id` | `#!python Optional[int]` | Optional. The group has been migrated to a supergroup with the specified identifier. This number may be greater than 32 bits and some programming languages may have difficulty/silent defects in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float type are safe for storing this identifier. |
| `migrate_from_chat_id` | `#!python Optional[int]` | Optional. The supergroup has been migrated from a group with the specified identifier. This number may be greater than 32 bits and some programming languages may have difficulty/silent defects in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float type are safe for storing this identifier. |
| `pinned_message` | `#!python Optional[Message]` | Optional. Specified message was pinned. Note that the Message object in this field will not contain further reply_to_message fields even if it is itself a reply. |
| `invoice` | `#!python Optional[Invoice]` | Optional. Message is an invoice for a payment, information about the invoice. |
| `successful_payment` | `#!python Optional[SuccessfulPayment]` | Optional. Message is a service message about a successful payment, information about the payment. |
| `connected_website` | `#!python Optional[str]` | Optional. The domain name of the website on which the user has logged in. |
| `passport_data` | `#!python Optional[PassportData]` | Optional. Telegram Passport data |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message. login_url buttons are represented as ordinary url buttons. |



## Location

- `from aiogram.types import Message`
- `from aiogram.api.types import Message`
- `from aiogram.api.types.message import Message`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#message)
- [aiogram.types.Poll](../types/poll.md)
- [aiogram.types.PassportData](../types/passport_data.md)
- [aiogram.types.Video](../types/video.md)
- [aiogram.types.MessageEntity](../types/message_entity.md)
- [aiogram.types.PhotoSize](../types/photo_size.md)
- [aiogram.types.Contact](../types/contact.md)
- [aiogram.types.Document](../types/document.md)
- [aiogram.types.Animation](../types/animation.md)
- [aiogram.types.SuccessfulPayment](../types/successful_payment.md)
- [aiogram.types.Chat](../types/chat.md)
- [aiogram.types.Audio](../types/audio.md)
- [aiogram.types.Game](../types/game.md)
- [aiogram.types.Voice](../types/voice.md)
- [aiogram.types.VideoNote](../types/video_note.md)
- [aiogram.types.Invoice](../types/invoice.md)
- [aiogram.types.Location](../types/location.md)
- [aiogram.types.Sticker](../types/sticker.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.User](../types/user.md)
- [aiogram.types.Venue](../types/venue.md)
