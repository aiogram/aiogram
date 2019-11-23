from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:  # pragma: no cover
    from .input_message_content import InputMessageContent
    from .inline_keyboard_markup import InlineKeyboardMarkup


class InlineQueryResultCachedMpeg4Gif(InlineQueryResult):
    """
    Represents a link to a video animation (H.264/MPEG-4 AVC video without sound) stored on the
    Telegram servers. By default, this animated MPEG-4 file will be sent by the user with an
    optional caption. Alternatively, you can use input_message_content to send a message with the
    specified content instead of the animation.

    Source: https://core.telegram.org/bots/api#inlinequeryresultcachedmpeg4gif
    """

    type: str = Field("mpeg4_gif", const=True)
    """Type of the result, must be mpeg4_gif"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    mpeg4_file_id: str
    """A valid file identifier for the MP4 file"""
    title: Optional[str] = None
    """Title for the result"""
    caption: Optional[str] = None
    """Caption of the MPEG-4 file to be sent, 0-1024 characters"""
    parse_mode: Optional[str] = None
    """Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or
    inline URLs in the media caption."""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """Content of the message to be sent instead of the video animation"""
