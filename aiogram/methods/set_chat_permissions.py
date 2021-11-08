from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Union

from ..types import ChatPermissions
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class SetChatPermissions(TelegramMethod[bool]):
    """
    Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the *can_restrict_members* administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setchatpermissions
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
    permissions: ChatPermissions
    """A JSON-serialized object for new default chat permissions"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="setChatPermissions", data=data)
