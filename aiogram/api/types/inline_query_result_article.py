from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:  # pragma: no cover
    from .input_message_content import InputMessageContent
    from .inline_keyboard_markup import InlineKeyboardMarkup


class InlineQueryResultArticle(InlineQueryResult):
    """
    Represents a link to an article or web page.

    Source: https://core.telegram.org/bots/api#inlinequeryresultarticle
    """

    type: str = Field("article", const=True)
    """Type of the result, must be article"""
    id: str
    """Unique identifier for this result, 1-64 Bytes"""
    title: str
    """Title of the result"""
    input_message_content: InputMessageContent
    """Content of the message to be sent"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
    url: Optional[str] = None
    """URL of the result"""
    hide_url: Optional[bool] = None
    """Pass True, if you don't want the URL to be shown in the message"""
    description: Optional[str] = None
    """Short description of the result"""
    thumb_url: Optional[str] = None
    """Url of the thumbnail for the result"""
    thumb_width: Optional[int] = None
    """Thumbnail width"""
    thumb_height: Optional[int] = None
    """Thumbnail height"""
