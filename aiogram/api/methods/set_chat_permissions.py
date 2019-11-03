from typing import Any, Dict, Union

from ..types import ChatPermissions
from .base import Request, TelegramMethod


class SetChatPermissions(TelegramMethod[bool]):
    """
    Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the can_restrict_members admin rights. Returns True on success.

    Source: https://core.telegram.org/bots/api#setchatpermissions
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)"""

    permissions: ChatPermissions
    """New default chat permissions"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})
        files: Dict[str, Any] = {}
        return Request(method="setChatPermissions", data=data, files=files)
