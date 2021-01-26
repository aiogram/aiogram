from __future__ import annotations

from .base import TelegramObject


class InputMessageContent(TelegramObject):
    """
    This object represents the content of a message to be sent as a result of an inline query. Telegram clients currently support the following 4 types:

     - :class:`aiogram.types.input_text_message_content.InputTextMessageContent`
     - :class:`aiogram.types.input_location_message_content.InputLocationMessageContent`
     - :class:`aiogram.types.input_venue_message_content.InputVenueMessageContent`
     - :class:`aiogram.types.input_contact_message_content.InputContactMessageContent`

    Source: https://core.telegram.org/bots/api#inputmessagecontent
    """
