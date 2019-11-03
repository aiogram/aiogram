from __future__ import annotations

from typing import Optional

from .input_message_content import InputMessageContent


class InputLocationMessageContent(InputMessageContent):
    """
    Represents the content of a location message to be sent as the result of an inline query.

    Source: https://core.telegram.org/bots/api#inputlocationmessagecontent
    """

    latitude: float
    """Latitude of the location in degrees"""
    longitude: float
    """Longitude of the location in degrees"""
    live_period: Optional[int] = None
    """Period in seconds for which the location can be updated, should be between 60 and 86400."""
