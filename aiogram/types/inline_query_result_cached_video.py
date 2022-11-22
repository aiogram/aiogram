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


class InlineQueryResultCachedVideo(InlineQueryResult):
    """
    Represents a link to a video file stored on the Telegram servers. By default, this video file will be sent by the user with an optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the video.

    Source: https://core.telegram.org/bots/api#inlinequeryresultcachedvideo
    """

    type: str = Field(InlineQueryResultType.VIDEO, const=True)
    """Type of the result, must be *video*"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    video_file_id: str
    """A valid file identifier for the video file"""
    title: str
    """Title for the result"""
    description: Optional[str] = None
    """*Optional*. Short description of the result"""
    caption: Optional[str] = None
    """*Optional*. Caption of the video to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """*Optional*. Mode for parsing entities in the video caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[List[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_ attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """*Optional*. Content of the message to be sent instead of the video"""
