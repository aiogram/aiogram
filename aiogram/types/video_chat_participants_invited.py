from __future__ import annotations

from typing import TYPE_CHECKING, List

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User


class VideoChatParticipantsInvited(TelegramObject):
    """
    This object represents a service message about new members invited to a video chat.

    Source: https://core.telegram.org/bots/api#videochatparticipantsinvited
    """

    users: List[User]
    """New members that were invited to the video chat"""
