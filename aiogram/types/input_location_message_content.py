from __future__ import annotations

from typing import Optional

from .input_message_content import InputMessageContent


class InputLocationMessageContent(InputMessageContent):
    """
    Represents the `content <https://core.telegram.org/bots/api#inputmessagecontent>`_ of a location message to be sent as the result of an inline query.

    Source: https://core.telegram.org/bots/api#inputlocationmessagecontent
    """

    latitude: float
    """Latitude of the location in degrees"""
    longitude: float
    """Longitude of the location in degrees"""
    horizontal_accuracy: Optional[float] = None
    """*Optional*. The radius of uncertainty for the location, measured in meters; 0-1500"""
    live_period: Optional[int] = None
    """*Optional*. Period in seconds for which the location can be updated, should be between 60 and 86400."""
    heading: Optional[int] = None
    """*Optional*. For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified."""
    proximity_alert_radius: Optional[int] = None
    """*Optional*. For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified."""
