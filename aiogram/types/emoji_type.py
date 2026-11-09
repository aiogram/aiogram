from .base import TelegramObject


class EmojiType(TelegramObject):
    """
    This object describes an emoji. Currently, it can be one of

     - :class:`aiogram.types.emoji_type_emoji.EmojiTypeEmoji`
     - :class:`aiogram.types.emoji_type_custom_emoji.EmojiTypeCustomEmoji`

    Source: https://core.telegram.org/bots/api#emojitype
    """
