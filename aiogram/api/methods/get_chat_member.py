from typing import Any, Dict, Union

from .base import Request, TelegramMethod
from ..types import ChatMember


class GetChatMember(TelegramMethod[ChatMember]):
    """
    Use this method to get information about a member of a chat. Returns a ChatMember object on success.

    Source: https://core.telegram.org/bots/api#getchatmember
    """

    __returning__ = ChatMember

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)"""

    user_id: int
    """Unique identifier of the target user"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})

        return Request(method="getChatMember", data=data)
