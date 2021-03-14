from __future__ import annotations

from typing import TYPE_CHECKING

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    pass


class VoiceChatStarted(TelegramObject):
    """
    This object represents a service message about a voice chat started in the chat. Currently holds no information.

    Source: https://core.telegram.org/bots/api#voicechatstarted
    """
