from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .input_message_content import InputMessageContent
    from .inline_keyboard_markup import InlineKeyboardMarkup


class InlineQueryResultVenue(InlineQueryResult):
    """
    Represents a venue. By default, the venue will be sent by the user. Alternatively, you can use
    input_message_content to send a message with the specified content instead of the venue.
    Note: This will only work in Telegram versions released after 9 April, 2016. Older clients
    will ignore them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultvenue
    """

    type: str = Field("venue", const=True)
    """Type of the result, must be venue"""
    id: str
    """Unique identifier for this result, 1-64 Bytes"""
    latitude: float
    """Latitude of the venue location in degrees"""
    longitude: float
    """Longitude of the venue location in degrees"""
    title: str
    """Title of the venue"""
    address: str
    """Address of the venue"""
    foursquare_id: Optional[str] = None
    """Foursquare identifier of the venue if known"""
    foursquare_type: Optional[str] = None
    """Foursquare type of the venue, if known. (For example, 'arts_entertainment/default',
    'arts_entertainment/aquarium' or 'food/icecream'.)"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """Content of the message to be sent instead of the venue"""
    thumb_url: Optional[str] = None
    """Url of the thumbnail for the result"""
    thumb_width: Optional[int] = None
    """Thumbnail width"""
    thumb_height: Optional[int] = None
    """Thumbnail height"""
