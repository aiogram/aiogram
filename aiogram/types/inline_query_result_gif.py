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


class InlineQueryResultGif(InlineQueryResult):
    """
    Represents a link to an animated GIF file. By default, this animated GIF file will be sent by the user with optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the animation.

    Source: https://core.telegram.org/bots/api#inlinequeryresultgif
    """

    type: str = Field(InlineQueryResultType.GIF, const=True)
    """Type of the result, must be *gif*"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    gif_url: str
    """A valid URL for the GIF file. File size must not exceed 1MB"""
    thumb_url: str
    """URL of the static (JPEG or GIF) or animated (MPEG4) thumbnail for the result"""
    gif_width: Optional[int] = None
    """*Optional*. Width of the GIF"""
    gif_height: Optional[int] = None
    """*Optional*. Height of the GIF"""
    gif_duration: Optional[int] = None
    """*Optional*. Duration of the GIF in seconds"""
    thumb_mime_type: Optional[str] = None
    """*Optional*. MIME type of the thumbnail, must be one of 'image/jpeg', 'image/gif', or 'video/mp4'. Defaults to 'image/jpeg'"""
    title: Optional[str] = None
    """*Optional*. Title for the result"""
    caption: Optional[str] = None
    """*Optional*. Caption of the GIF file to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """*Optional*. Mode for parsing entities in the caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[List[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_ attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """*Optional*. Content of the message to be sent instead of the GIF animation"""
