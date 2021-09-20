from __future__ import annotations

from typing import TYPE_CHECKING

from .base import TelegramObject

if TYPE_CHECKING:
    from .location import Location


class ChatLocation(TelegramObject):
    """
    Represents a location to which a chat is connected.

    Source: https://core.telegram.org/bots/api#chatlocation
    """

    location: Location
    """The location to which the supergroup is connected. Can't be a live location."""
    address: str
    """Location address; 1-64 characters, as defined by the chat owner"""
