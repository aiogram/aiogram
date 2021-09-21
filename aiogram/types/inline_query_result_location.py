from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_message_content import InputMessageContent


class InlineQueryResultLocation(InlineQueryResult):
    """
    Represents a location on a map. By default, the location will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the location.
    **Note:** This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultlocation
    """

    type: str = Field("location", const=True)
    """Type of the result, must be *location*"""
    id: str
    """Unique identifier for this result, 1-64 Bytes"""
    latitude: float
    """Location latitude in degrees"""
    longitude: float
    """Location longitude in degrees"""
    title: str
    """Location title"""
    horizontal_accuracy: Optional[float] = None
    """*Optional*. The radius of uncertainty for the location, measured in meters; 0-1500"""
    live_period: Optional[int] = None
    """*Optional*. Period in seconds for which the location can be updated, should be between 60 and 86400."""
    heading: Optional[int] = None
    """*Optional*. For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified."""
    proximity_alert_radius: Optional[int] = None
    """*Optional*. For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified."""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_ attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """*Optional*. Content of the message to be sent instead of the location"""
    thumb_url: Optional[str] = None
    """*Optional*. Url of the thumbnail for the result"""
    thumb_width: Optional[int] = None
    """*Optional*. Thumbnail width"""
    thumb_height: Optional[int] = None
    """*Optional*. Thumbnail height"""
