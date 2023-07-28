from __future__ import annotations

from typing import Union

from ..types import (
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
)
from .base import TelegramMethod


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
    __api_method__ = "getChatMember"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)"""
    user_id: int
    """Unique identifier of the target user"""
