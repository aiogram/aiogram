from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_message_content import InputMessageContent


class InlineQueryResultArticle(InlineQueryResult):
    """
    Represents a link to an article or web page.

    Source: https://core.telegram.org/bots/api#inlinequeryresultarticle
    """

    type: str = Field("article", const=True)
    """Type of the result, must be *article*"""
    id: str
    """Unique identifier for this result, 1-64 Bytes"""
    title: str
    """Title of the result"""
    input_message_content: InputMessageContent
    """Content of the message to be sent"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_ attached to the message"""
    url: Optional[str] = None
    """*Optional*. URL of the result"""
    hide_url: Optional[bool] = None
    """*Optional*. Pass :code:`True`, if you don't want the URL to be shown in the message"""
    description: Optional[str] = None
    """*Optional*. Short description of the result"""
    thumb_url: Optional[str] = None
    """*Optional*. Url of the thumbnail for the result"""
    thumb_width: Optional[int] = None
    """*Optional*. Thumbnail width"""
    thumb_height: Optional[int] = None
    """*Optional*. Thumbnail height"""
