from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Union

from ..types import (
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
)
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class GetChatAdministrators(
    TelegramMethod[
        List[
            Union[
                ChatMemberOwner,
                ChatMemberAdministrator,
                ChatMemberMember,
                ChatMemberRestricted,
                ChatMemberLeft,
                ChatMemberBanned,
            ]
        ]
    ]
):
    """
    Use this method to get a list of administrators in a chat. On success, returns an Array of :class:`aiogram.types.chat_member.ChatMember` objects that contains information about all chat administrators except other bots. If the chat is a group or a supergroup and no administrators were appointed, only the creator will be returned.

    Source: https://core.telegram.org/bots/api#getchatadministrators
    """

    __returning__ = List[
        Union[
            ChatMemberOwner,
            ChatMemberAdministrator,
            ChatMemberMember,
            ChatMemberRestricted,
            ChatMemberLeft,
            ChatMemberBanned,
        ]
    ]

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getChatAdministrators", data=data)
