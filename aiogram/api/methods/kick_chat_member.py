import datetime
from typing import Any, Dict, Optional, Union

from .base import Request, TelegramMethod


class KickChatMember(TelegramMethod[bool]):
    """
    Use this method to kick a user from a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the group on their own using invite links, etc., unless unbanned first. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.

    Source: https://core.telegram.org/bots/api#kickchatmember
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target group or username of the target supergroup or channel (in the format @channelusername)"""

    user_id: int
    """Unique identifier of the target user"""

    until_date: Optional[Union[int, datetime.datetime, datetime.timedelta]] = None
    """Date when the user will be unbanned, unix time. If user is banned for more than 366 days or less than 30 seconds from the current time they are considered to be banned forever"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="kickChatMember", data=data)
