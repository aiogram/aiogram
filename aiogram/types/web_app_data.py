from __future__ import annotations

from .base import TelegramObject


class WebAppData(TelegramObject):
    """
    Describes data sent from a `Web App <https://core.telegram.org/bots/webapps>`_ to the bot.

    Source: https://core.telegram.org/bots/api#webappdata
    """

    data: str
    """The data. Be aware that a bad client can send arbitrary data in this field."""
    button_text: str
    """Text of the *web_app* keyboard button from which the Web App was opened. Be aware that a bad client can send arbitrary data in this field."""
