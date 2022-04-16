from __future__ import annotations

from typing import TYPE_CHECKING

from .base import TelegramObject

if TYPE_CHECKING:
    pass


class VideoChatStarted(TelegramObject):
    """
    This object represents a service message about a video chat started in the chat. Currently holds no information.

    Source: https://core.telegram.org/bots/api#videochatstarted
    """
