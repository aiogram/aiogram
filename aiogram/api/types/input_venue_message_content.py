from __future__ import annotations

from typing import Optional

from .input_message_content import InputMessageContent


class InputVenueMessageContent(InputMessageContent):
    """
    Represents the content of a venue message to be sent as the result of an inline query.

    Source: https://core.telegram.org/bots/api#inputvenuemessagecontent
    """

    latitude: float
    """Latitude of the venue in degrees"""
    longitude: float
    """Longitude of the venue in degrees"""
    title: str
    """Name of the venue"""
    address: str
    """Address of the venue"""
    foursquare_id: Optional[str] = None
    """Foursquare identifier of the venue, if known"""
    foursquare_type: Optional[str] = None
    """Foursquare type of the venue, if known. (For example, 'arts_entertainment/default',
    'arts_entertainment/aquarium' or 'food/icecream'.)"""
