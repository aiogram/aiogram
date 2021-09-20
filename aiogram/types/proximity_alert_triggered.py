from __future__ import annotations

from typing import TYPE_CHECKING

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User


class ProximityAlertTriggered(TelegramObject):
    """
    This object represents the content of a service message, sent whenever a user in the chat triggers a proximity alert set by another user.

    Source: https://core.telegram.org/bots/api#proximityalerttriggered
    """

    traveler: User
    """User that triggered the alert"""
    watcher: User
    """User that set the alert"""
    distance: int
    """The distance between the users"""
