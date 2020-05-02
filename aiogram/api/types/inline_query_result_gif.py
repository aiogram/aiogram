from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:  # pragma: no cover
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_message_content import InputMessageContent


class InlineQueryResultGif(InlineQueryResult):
    """
    Represents a link to an animated GIF file. By default, this animated GIF file will be sent by
    the user with optional caption. Alternatively, you can use input_message_content to send a
    message with the specified content instead of the animation.

    Source: https://core.telegram.org/bots/api#inlinequeryresultgif
    """

    type: str = Field("gif", const=True)
    """Type of the result, must be gif"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    gif_url: str
    """A valid URL for the GIF file. File size must not exceed 1MB"""
    thumb_url: str
    """URL of the static thumbnail for the result (jpeg or gif)"""
    gif_width: Optional[int] = None
    """Width of the GIF"""
    gif_height: Optional[int] = None
    """Height of the GIF"""
    gif_duration: Optional[int] = None
    """Duration of the GIF"""
    title: Optional[str] = None
    """Title for the result"""
    caption: Optional[str] = None
    """Caption of the GIF file to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = None
    """Mode for parsing entities in the caption. See formatting options for more details."""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """Content of the message to be sent instead of the GIF animation"""
