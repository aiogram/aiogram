from typing import Any, Dict, Union

from .base import Request, TelegramMethod


class UnbanChatMember(TelegramMethod[bool]):
    """
    Use this method to unban a previously kicked user in a supergroup or channel. The user will not return to the group or channel automatically, but will be able to join via link, etc. The bot must be an administrator for this to work. Returns True on success.

    Source: https://core.telegram.org/bots/api#unbanchatmember
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target group or username of the target supergroup or channel (in the format @username)"""

    user_id: int
    """Unique identifier of the target user"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})

        return Request(method="unbanChatMember", data=data)
