from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional, Union

from ..enums import InlineQueryResultType
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_contact_message_content import InputContactMessageContent
    from .input_invoice_message_content import InputInvoiceMessageContent
    from .input_location_message_content import InputLocationMessageContent
    from .input_text_message_content import InputTextMessageContent
    from .input_venue_message_content import InputVenueMessageContent


class InlineQueryResultLocation(InlineQueryResult):
    """
    Represents a location on a map. By default, the location will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the location.
    **Note:** This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultlocation
    """

    type: Literal[InlineQueryResultType.LOCATION] = InlineQueryResultType.LOCATION
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
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_ attached to the message"""
    input_message_content: Optional[
        Union[
            InputTextMessageContent,
            InputLocationMessageContent,
            InputVenueMessageContent,
            InputContactMessageContent,
            InputInvoiceMessageContent,
        ]
    ] = None
    """*Optional*. Content of the message to be sent instead of the location"""
    thumbnail_url: Optional[str] = None
    """*Optional*. Url of the thumbnail for the result"""
    thumbnail_width: Optional[int] = None
    """*Optional*. Thumbnail width"""
    thumbnail_height: Optional[int] = None
    """*Optional*. Thumbnail height"""
