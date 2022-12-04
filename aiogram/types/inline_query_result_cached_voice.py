from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from pydantic import Field

from ..enums import InlineQueryResultType
from .base import UNSET
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_message_content import InputMessageContent
    from .message_entity import MessageEntity


class InlineQueryResultCachedVoice(InlineQueryResult):
    """
    Represents a link to a voice message stored on the Telegram servers. By default, this voice message will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the voice message.
    **Note:** This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultcachedvoice
    """

    type: str = Field(InlineQueryResultType.VOICE, const=True)
    """Type of the result, must be *voice*"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    voice_file_id: str
    """A valid file identifier for the voice message"""
    title: str
    """Voice message title"""
    caption: Optional[str] = None
    """*Optional*. Caption, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """*Optional*. Mode for parsing entities in the voice message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[List[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_ attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """*Optional*. Content of the message to be sent instead of the voice message"""
