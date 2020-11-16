from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    from .location import Location


class Venue(TelegramObject):
    """
    This object represents a venue.

    Source: https://core.telegram.org/bots/api#venue
    """

    location: Location
    """Venue location. Can't be a live location"""
    title: str
    """Name of the venue"""
    address: str
    """Address of the venue"""
    foursquare_id: Optional[str] = None
    """Foursquare identifier of the venue"""
    foursquare_type: Optional[str] = None
    """Foursquare type of the venue. (For example, 'arts_entertainment/default',
    'arts_entertainment/aquarium' or 'food/icecream'.)"""
    google_place_id: Optional[str] = None
    """Google Places identifier of the venue"""
    google_place_type: Optional[str] = None
    """Google Places type of the venue. (See supported types.)"""
