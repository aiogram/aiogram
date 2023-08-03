from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject


class Location(TelegramObject):
    """
    This object represents a point on the map.

    Source: https://core.telegram.org/bots/api#location
    """

    longitude: float
    """Longitude as defined by sender"""
    latitude: float
    """Latitude as defined by sender"""
    horizontal_accuracy: Optional[float] = None
    """*Optional*. The radius of uncertainty for the location, measured in meters; 0-1500"""
    live_period: Optional[int] = None
    """*Optional*. Time relative to the message sending date, during which the location can be updated; in seconds. For active live locations only."""
    heading: Optional[int] = None
    """*Optional*. The direction in which user is moving, in degrees; 1-360. For active live locations only."""
    proximity_alert_radius: Optional[int] = None
    """*Optional*. The maximum distance for proximity alerts about approaching another chat member, in meters. For sent live locations only."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            longitude: float,
            latitude: float,
            horizontal_accuracy: Optional[float] = None,
            live_period: Optional[int] = None,
            heading: Optional[int] = None,
            proximity_alert_radius: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                longitude=longitude,
                latitude=latitude,
                horizontal_accuracy=horizontal_accuracy,
                live_period=live_period,
                heading=heading,
                proximity_alert_radius=proximity_alert_radius,
                **__pydantic_kwargs,
            )
