from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Union

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class LeaveChat(TelegramMethod[bool]):
    """
    Use this method for your bot to leave a group, supergroup or channel. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#leavechat
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="leaveChat", data=data)
