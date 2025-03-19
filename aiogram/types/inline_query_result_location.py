from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional

from ..enums import InlineQueryResultType
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_message_content_union import InputMessageContentUnion


class InlineQueryResultLocation(InlineQueryResult):
    """
    Represents a location on a map. By default, the location will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the location.

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
    """*Optional*. Period in seconds during which the location can be updated, should be between 60 and 86400, or 0x7FFFFFFF for live locations that can be edited indefinitely."""
    heading: Optional[int] = None
    """*Optional*. For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified."""
    proximity_alert_radius: Optional[int] = None
    """*Optional*. For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified."""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_ attached to the message"""
    input_message_content: Optional[InputMessageContentUnion] = None
    """*Optional*. Content of the message to be sent instead of the location"""
    thumbnail_url: Optional[str] = None
    """*Optional*. Url of the thumbnail for the result"""
    thumbnail_width: Optional[int] = None
    """*Optional*. Thumbnail width"""
    thumbnail_height: Optional[int] = None
    """*Optional*. Thumbnail height"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InlineQueryResultType.LOCATION] = InlineQueryResultType.LOCATION,
            id: str,
            latitude: float,
            longitude: float,
            title: str,
            horizontal_accuracy: Optional[float] = None,
            live_period: Optional[int] = None,
            heading: Optional[int] = None,
            proximity_alert_radius: Optional[int] = None,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            input_message_content: Optional[InputMessageContentUnion] = None,
            thumbnail_url: Optional[str] = None,
            thumbnail_width: Optional[int] = None,
            thumbnail_height: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                id=id,
                latitude=latitude,
                longitude=longitude,
                title=title,
                horizontal_accuracy=horizontal_accuracy,
                live_period=live_period,
                heading=heading,
                proximity_alert_radius=proximity_alert_radius,
                reply_markup=reply_markup,
                input_message_content=input_message_content,
                thumbnail_url=thumbnail_url,
                thumbnail_width=thumbnail_width,
                thumbnail_height=thumbnail_height,
                **__pydantic_kwargs,
            )
