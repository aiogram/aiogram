from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .base import UNSET
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:  # pragma: no cover
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_message_content import InputMessageContent


class InlineQueryResultCachedVideo(InlineQueryResult):
    """
    Represents a link to a video file stored on the Telegram servers. By default, this video file
    will be sent by the user with an optional caption. Alternatively, you can use
    input_message_content to send a message with the specified content instead of the video.

    Source: https://core.telegram.org/bots/api#inlinequeryresultcachedvideo
    """

    type: str = Field("video", const=True)
    """Type of the result, must be video"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    video_file_id: str
    """A valid file identifier for the video file"""
    title: str
    """Title for the result"""
    description: Optional[str] = None
    """Short description of the result"""
    caption: Optional[str] = None
    """Caption of the video to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or
    inline URLs in the media caption."""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """Content of the message to be sent instead of the video"""
