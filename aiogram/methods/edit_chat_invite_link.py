from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import ChatInviteLink
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class EditChatInviteLink(TelegramMethod[ChatInviteLink]):
    """
    Use this method to edit a non-primary invite link created by the bot. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns the edited invite link as a :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.

    Source: https://core.telegram.org/bots/api#editchatinvitelink
    """

    __returning__ = ChatInviteLink

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    invite_link: str
    """The invite link to edit"""
    expire_date: Optional[int] = None
    """Point in time (Unix timestamp) when the link will expire"""
    member_limit: Optional[int] = None
    """Maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="editChatInviteLink", data=data)
