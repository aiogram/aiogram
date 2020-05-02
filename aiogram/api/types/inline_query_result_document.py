from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:  # pragma: no cover
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_message_content import InputMessageContent


class InlineQueryResultDocument(InlineQueryResult):
    """
    Represents a link to a file. By default, this file will be sent by the user with an optional
    caption. Alternatively, you can use input_message_content to send a message with the specified
    content instead of the file. Currently, only .PDF and .ZIP files can be sent using this
    method.
    Note: This will only work in Telegram versions released after 9 April, 2016. Older clients
    will ignore them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultdocument
    """

    type: str = Field("document", const=True)
    """Type of the result, must be document"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    title: str
    """Title for the result"""
    document_url: str
    """A valid URL for the file"""
    mime_type: str
    """Mime type of the content of the file, either 'application/pdf' or 'application/zip'"""
    caption: Optional[str] = None
    """Caption of the document to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = None
    """Mode for parsing entities in the document caption. See formatting options for more details."""
    description: Optional[str] = None
    """Short description of the result"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """Content of the message to be sent instead of the file"""
    thumb_url: Optional[str] = None
    """URL of the thumbnail (jpeg only) for the file"""
    thumb_width: Optional[int] = None
    """Thumbnail width"""
    thumb_height: Optional[int] = None
    """Thumbnail height"""
