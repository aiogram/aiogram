from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .input_message_content import InputMessageContent
    from .inline_keyboard_markup import InlineKeyboardMarkup


class InlineQueryResultLocation(InlineQueryResult):
    """
    Represents a location on a map. By default, the location will be sent by the user.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the location.
    Note: This will only work in Telegram versions released after 9 April, 2016. Older clients
    will ignore them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultlocation
    """

    type: str = Field("location", const=True)
    """Type of the result, must be location"""
    id: str
    """Unique identifier for this result, 1-64 Bytes"""
    latitude: float
    """Location latitude in degrees"""
    longitude: float
    """Location longitude in degrees"""
    title: str
    """Location title"""
    live_period: Optional[int] = None
    """Period in seconds for which the location can be updated, should be between 60 and 86400."""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """Content of the message to be sent instead of the location"""
    thumb_url: Optional[str] = None
    """Url of the thumbnail for the result"""
    thumb_width: Optional[int] = None
    """Thumbnail width"""
    thumb_height: Optional[int] = None
    """Thumbnail height"""
