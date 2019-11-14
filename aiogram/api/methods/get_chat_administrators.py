from typing import Any, Dict, List, Union

from ..types import ChatMember
from .base import Request, TelegramMethod


class GetChatAdministrators(TelegramMethod[List[ChatMember]]):
    """
    Use this method to get a list of administrators in a chat. On success, returns an Array of ChatMember objects that contains information about all chat administrators except other bots. If the chat is a group or a supergroup and no administrators were appointed, only the creator will be returned.

    Source: https://core.telegram.org/bots/api#getchatadministrators
    """

    __returning__ = List[ChatMember]

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getChatAdministrators", data=data)
