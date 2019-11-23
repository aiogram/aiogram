from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:  # pragma: no cover
    from .input_message_content import InputMessageContent
    from .inline_keyboard_markup import InlineKeyboardMarkup


class InlineQueryResultCachedPhoto(InlineQueryResult):
    """
    Represents a link to a photo stored on the Telegram servers. By default, this photo will be
    sent by the user with an optional caption. Alternatively, you can use input_message_content to
    send a message with the specified content instead of the photo.

    Source: https://core.telegram.org/bots/api#inlinequeryresultcachedphoto
    """

    type: str = Field("photo", const=True)
    """Type of the result, must be photo"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    photo_file_id: str
    """A valid file identifier of the photo"""
    title: Optional[str] = None
    """Title for the result"""
    description: Optional[str] = None
    """Short description of the result"""
    caption: Optional[str] = None
    """Caption of the photo to be sent, 0-1024 characters"""
    parse_mode: Optional[str] = None
    """Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or
    inline URLs in the media caption."""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """Content of the message to be sent instead of the photo"""
