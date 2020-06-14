from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .base import UNSET
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:  # pragma: no cover
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_message_content import InputMessageContent


class InlineQueryResultMpeg4Gif(InlineQueryResult):
    """
    Represents a link to a video animation (H.264/MPEG-4 AVC video without sound). By default,
    this animated MPEG-4 file will be sent by the user with optional caption. Alternatively, you
    can use input_message_content to send a message with the specified content instead of the
    animation.

    Source: https://core.telegram.org/bots/api#inlinequeryresultmpeg4gif
    """

    type: str = Field("mpeg4_gif", const=True)
    """Type of the result, must be mpeg4_gif"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    mpeg4_url: str
    """A valid URL for the MP4 file. File size must not exceed 1MB"""
    thumb_url: str
    """URL of the static (JPEG or GIF) or animated (MPEG4) thumbnail for the result"""
    mpeg4_width: Optional[int] = None
    """Video width"""
    mpeg4_height: Optional[int] = None
    """Video height"""
    mpeg4_duration: Optional[int] = None
    """Video duration"""
    thumb_mime_type: Optional[str] = None
    """MIME type of the thumbnail, must be one of 'image/jpeg', 'image/gif', or 'video/mp4'.
    Defaults to 'image/jpeg'"""
    title: Optional[str] = None
    """Title for the result"""
    caption: Optional[str] = None
    """Caption of the MPEG-4 file to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """Mode for parsing entities in the caption. See formatting options for more details."""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """Content of the message to be sent instead of the video animation"""
