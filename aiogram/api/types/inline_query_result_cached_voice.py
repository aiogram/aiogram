from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .base import UNSET
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:  # pragma: no cover
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_message_content import InputMessageContent


class InlineQueryResultCachedVoice(InlineQueryResult):
    """
    Represents a link to a voice message stored on the Telegram servers. By default, this voice
    message will be sent by the user. Alternatively, you can use input_message_content to send a
    message with the specified content instead of the voice message.
    Note: This will only work in Telegram versions released after 9 April, 2016. Older clients
    will ignore them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultcachedvoice
    """

    type: str = Field("voice", const=True)
    """Type of the result, must be voice"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    voice_file_id: str
    """A valid file identifier for the voice message"""
    title: str
    """Voice message title"""
    caption: Optional[str] = None
    """Caption, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or
    inline URLs in the media caption."""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """Content of the message to be sent instead of the voice message"""
