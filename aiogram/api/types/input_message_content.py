from __future__ import annotations

from .base import TelegramObject


class InputMessageContent(TelegramObject):
    """
    This object represents the content of a message to be sent as a result of an inline query.
    Telegram clients currently support the following 4 types:
     - InputTextMessageContent
     - InputLocationMessageContent
     - InputVenueMessageContent
     - InputContactMessageContent

    Source: https://core.telegram.org/bots/api#inputmessagecontent
    """
