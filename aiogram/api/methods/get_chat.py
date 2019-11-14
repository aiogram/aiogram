from typing import Any, Dict, Union

from ..types import Chat
from .base import Request, TelegramMethod


class GetChat(TelegramMethod[Chat]):
    """
    Use this method to get up to date information about the chat (current name of the user for
    one-on-one conversations, current username of a user, group or channel, etc.). Returns a Chat
    object on success.

    Source: https://core.telegram.org/bots/api#getchat
    """

    __returning__ = Chat

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in
    the format @channelusername)"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getChat", data=data)
