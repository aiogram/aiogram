from __future__ import annotations

from typing import Optional

from .input_message_content import InputMessageContent


class InputVenueMessageContent(InputMessageContent):
    """
    Represents the `content <https://core.telegram.org/bots/api#inputmessagecontent>`_ of a venue message to be sent as the result of an inline query.

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
    """*Optional*. Foursquare identifier of the venue, if known"""
    foursquare_type: Optional[str] = None
    """*Optional*. Foursquare type of the venue, if known. (For example, 'arts_entertainment/default', 'arts_entertainment/aquarium' or 'food/icecream'.)"""
    google_place_id: Optional[str] = None
    """*Optional*. Google Places identifier of the venue"""
    google_place_type: Optional[str] = None
    """*Optional*. Google Places type of the venue. (See `supported types <https://developers.google.com/places/web-service/supported_types>`_.)"""
