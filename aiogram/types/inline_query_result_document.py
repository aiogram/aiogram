from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from pydantic import Field

from .base import UNSET
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_message_content import InputMessageContent
    from .message_entity import MessageEntity


class InlineQueryResultDocument(InlineQueryResult):
    """
    Represents a link to a file. By default, this file will be sent by the user with an optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the file. Currently, only **.PDF** and **.ZIP** files can be sent using this method.
    **Note:** This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultdocument
    """

    type: str = Field("document", const=True)
    """Type of the result, must be *document*"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    title: str
    """Title for the result"""
    document_url: str
    """A valid URL for the file"""
    mime_type: str
    """MIME type of the content of the file, either 'application/pdf' or 'application/zip'"""
    caption: Optional[str] = None
    """*Optional*. Caption of the document to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """*Optional*. Mode for parsing entities in the document caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[List[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    description: Optional[str] = None
    """*Optional*. Short description of the result"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. Inline keyboard attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """*Optional*. Content of the message to be sent instead of the file"""
    thumb_url: Optional[str] = None
    """*Optional*. URL of the thumbnail (JPEG only) for the file"""
    thumb_width: Optional[int] = None
    """*Optional*. Thumbnail width"""
    thumb_height: Optional[int] = None
    """*Optional*. Thumbnail height"""
