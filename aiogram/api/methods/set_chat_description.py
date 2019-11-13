from typing import Any, Dict, Optional, Union

from .base import Request, TelegramMethod


class SetChatDescription(TelegramMethod[bool]):
    """
    Use this method to change the description of a group, a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.

    Source: https://core.telegram.org/bots/api#setchatdescription
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format @channelusername)"""

    description: Optional[str] = None
    """New chat description, 0-255 characters"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})

        return Request(method="setChatDescription", data=data)
