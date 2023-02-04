from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Union

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


class GetChatMember(
    TelegramMethod[
        Union[
            ChatMemberOwner,
            ChatMemberAdministrator,
            ChatMemberMember,
            ChatMemberRestricted,
            ChatMemberLeft,
            ChatMemberBanned,
        ]
    ]
):
    """
    Use this method to get information about a member of a chat. The method is only guaranteed to work for other users if the bot is an administrator in the chat. Returns a :class:`aiogram.types.chat_member.ChatMember` object on success.

    Source: https://core.telegram.org/bots/api#getchatmember
    """

    __returning__ = Union[
        ChatMemberOwner,
        ChatMemberAdministrator,
        ChatMemberMember,
        ChatMemberRestricted,
        ChatMemberLeft,
        ChatMemberBanned,
    ]

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)"""
    user_id: int
    """Unique identifier of the target user"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getChatMember", data=data)
