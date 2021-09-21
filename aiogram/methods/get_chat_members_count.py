from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Union

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class GetChatMembersCount(TelegramMethod[int]):
    """
    .. warning:

        Renamed from :code:`getChatMembersCount` in 5.3 bot API version and can be removed in near future

    Use this method to get the number of members in a chat. Returns *Int* on success.

    Source: https://core.telegram.org/bots/api#getchatmembercount
    """

    __returning__ = int

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getChatMembersCount", data=data)
