from typing import Any, Dict, Optional, Union

from .base import Request, TelegramMethod
from ..types import Message


class ForwardMessage(TelegramMethod[Message]):
    """
    Use this method to forward messages of any kind. On success, the sent Message is returned.

    Source: https://core.telegram.org/bots/api#forwardmessage
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format @channelusername)"""

    from_chat_id: Union[int, str]
    """Unique identifier for the chat where the original message was sent (or channel username in the format @channelusername)"""

    message_id: int
    """Message identifier in the chat specified in from_chat_id"""

    disable_notification: Optional[bool] = None
    """Sends the message silently. Users will receive a notification with no sound."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})

        return Request(method="forwardMessage", data=data)
