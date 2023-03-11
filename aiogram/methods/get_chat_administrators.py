from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

from ..types import (
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
)
from .base import TelegramMethod


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
    Use this method to get a list of administrators in a chat, which aren't bots. Returns an Array of :class:`aiogram.types.chat_member.ChatMember` objects.

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
    __api_method__ = "getChatAdministrators"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)"""
