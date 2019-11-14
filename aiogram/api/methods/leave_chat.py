from typing import Any, Dict, Union

from .base import Request, TelegramMethod


class LeaveChat(TelegramMethod[bool]):
    """
    Use this method for your bot to leave a group, supergroup or channel. Returns True on success.

    Source: https://core.telegram.org/bots/api#leavechat
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="leaveChat", data=data)
