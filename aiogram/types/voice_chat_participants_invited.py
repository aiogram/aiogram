from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User


class VoiceChatParticipantsInvited(TelegramObject):
    """
    This object represents a service message about new members invited to a voice chat.

    Source: https://core.telegram.org/bots/api#voicechatparticipantsinvited
    """

    users: Optional[List[User]] = None
    """*Optional*. New members that were invited to the voice chat"""
