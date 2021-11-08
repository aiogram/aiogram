from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class KickChatMember(TelegramMethod[bool]):
    """
    .. warning:

        Renamed from :code:`kickChatMember` in 5.3 bot API version and can be removed in near future

    Use this method to ban a user in a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the chat on their own using invite links, etc., unless `unbanned <https://core.telegram.org/bots/api#unbanchatmember>`_ first. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#banchatmember
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target group or username of the target supergroup or channel (in the format :code:`@channelusername`)"""
    user_id: int
    """Unique identifier of the target user"""
    until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None
    """Date when the user will be unbanned, unix time. If user is banned for more than 366 days or less than 30 seconds from the current time they are considered to be banned forever. Applied for supergroups and channels only."""
    revoke_messages: Optional[bool] = None
    """Pass :code:`True` to delete all messages from the chat for the user that is being removed. If :code:`False`, the user will be able to see messages in the group that were sent before the user was removed. Always :code:`True` for supergroups and channels."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="kickChatMember", data=data)
