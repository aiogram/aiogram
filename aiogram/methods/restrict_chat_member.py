from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import ChatPermissions
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class RestrictChatMember(TelegramMethod[bool]):
    """
    Use this method to restrict a user in a supergroup. The bot must be an administrator in the supergroup for this to work and must have the appropriate admin rights. Pass :code:`True` for all permissions to lift restrictions from a user. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#restrictchatmember
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
    user_id: int
    """Unique identifier of the target user"""
    permissions: ChatPermissions
    """A JSON-serialized object for new user permissions"""
    until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None
    """Date when restrictions will be lifted for the user, unix time. If user is restricted for more than 366 days or less than 30 seconds from the current time, they are considered to be restricted forever"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="restrictChatMember", data=data)
