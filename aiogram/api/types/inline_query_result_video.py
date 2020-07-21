from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .base import UNSET
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:  # pragma: no cover
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_message_content import InputMessageContent


class InlineQueryResultVideo(InlineQueryResult):
    """
    Represents a link to a page containing an embedded video player or a video file. By default,
    this video file will be sent by the user with an optional caption. Alternatively, you can use
    input_message_content to send a message with the specified content instead of the video.
    If an InlineQueryResultVideo message contains an embedded video (e.g., YouTube), you must
    replace its content using input_message_content.

    Source: https://core.telegram.org/bots/api#inlinequeryresultvideo
    """

    type: str = Field("video", const=True)
    """Type of the result, must be video"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    video_url: str
    """A valid URL for the embedded video player or video file"""
    mime_type: str
    """Mime type of the content of video url, 'text/html' or 'video/mp4'"""
    thumb_url: str
    """URL of the thumbnail (jpeg only) for the video"""
    title: str
    """Title for the result"""
    caption: Optional[str] = None
    """Caption of the video to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """Mode for parsing entities in the video caption. See formatting options for more details."""
    video_width: Optional[int] = None
    """Video width"""
    video_height: Optional[int] = None
    """Video height"""
    video_duration: Optional[int] = None
    """Video duration in seconds"""
    description: Optional[str] = None
    """Short description of the result"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """Content of the message to be sent instead of the video. This field is required if
    InlineQueryResultVideo is used to send an HTML-page as a result (e.g., a YouTube video)."""
