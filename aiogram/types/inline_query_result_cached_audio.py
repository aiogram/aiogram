from __future__ import annotations

from typing import TYPE_CHECKING, List, Literal, Optional, Union

from ..enums import InlineQueryResultType
from .base import UNSET_PARSE_MODE
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_contact_message_content import InputContactMessageContent
    from .input_invoice_message_content import InputInvoiceMessageContent
    from .input_location_message_content import InputLocationMessageContent
    from .input_text_message_content import InputTextMessageContent
    from .input_venue_message_content import InputVenueMessageContent
    from .message_entity import MessageEntity


class InlineQueryResultCachedAudio(InlineQueryResult):
    """
    Represents a link to an MP3 audio file stored on the Telegram servers. By default, this audio file will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the audio.
    **Note:** This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultcachedaudio
    """

    type: Literal[InlineQueryResultType.AUDIO] = InlineQueryResultType.AUDIO
    """Type of the result, must be *audio*"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    audio_file_id: str
    """A valid file identifier for the audio file"""
    caption: Optional[str] = None
    """*Optional*. Caption, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET_PARSE_MODE
    """*Optional*. Mode for parsing entities in the audio caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[List[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_ attached to the message"""
    input_message_content: Optional[
        Union[
            InputTextMessageContent,
            InputLocationMessageContent,
            InputVenueMessageContent,
            InputContactMessageContent,
            InputInvoiceMessageContent,
        ]
    ] = None
    """*Optional*. Content of the message to be sent instead of the audio"""
