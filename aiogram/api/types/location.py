from __future__ import annotations

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
