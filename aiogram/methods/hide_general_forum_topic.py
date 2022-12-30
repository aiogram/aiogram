from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Union

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class HideGeneralForumTopic(TelegramMethod[bool]):
    """
    Use this method to hide the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. The topic will be automatically closed if it was open. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#hidegeneralforumtopic
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="hideGeneralForumTopic", data=data)
