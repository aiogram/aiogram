from ..types import ChatShareThemeBackdrops
from .base import TelegramMethod


class GetChatShareThemeBackdrops(TelegramMethod[ChatShareThemeBackdrops]):
    """
    Use this method to get the list of backdrops, which can be used as the background of a theme of the screen for sharing a link to a user or a chat. Requires no parameters. Returns a :class:`aiogram.types.chat_share_theme_backdrops.ChatShareThemeBackdrops` object.

    Source: https://core.telegram.org/bots/api#getchatsharethemebackdrops
    """

    __returning__ = ChatShareThemeBackdrops
    __api_method__ = "getChatShareThemeBackdrops"
