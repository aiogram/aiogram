from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class UnbanChatMember(TelegramMethod[bool]):
    """
    Use this method to unban a previously banned user in a supergroup or channel. The user will **not** return to the group or channel automatically, but will be able to join via link, etc. The bot must be an administrator for this to work. By default, this method guarantees that after the call the user is not a member of the chat, but will be able to join it. So if the user is a member of the chat they will also be **removed** from the chat. If you don't want this, use the parameter *only_if_banned*. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#unbanchatmember
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target group or username of the target supergroup or channel (in the format :code:`@channelusername`)"""
    user_id: int
    """Unique identifier of the target user"""
    only_if_banned: Optional[bool] = None
    """Do nothing if the user is not banned"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="unbanChatMember", data=data)
