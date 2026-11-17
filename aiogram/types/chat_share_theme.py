from .base import TelegramObject


class ChatShareTheme(TelegramObject):
    """
    This object describes the theme of the screen for sharing a link to a user or a chat. Currently, it can be one of

     - :class:`aiogram.types.chat_share_theme_emoji.ChatShareThemeEmoji`
     - :class:`aiogram.types.chat_share_theme_unique_gift.ChatShareThemeUniqueGift`

    Source: https://core.telegram.org/bots/api#chatsharetheme
    """
