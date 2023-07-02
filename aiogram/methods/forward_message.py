from __future__ import annotations

from typing import Optional, Union

from ..types import Message
from ..types.base import UNSET_PROTECT_CONTENT
from .base import TelegramMethod


class ForwardMessage(TelegramMethod[Message]):
    """
    Use this method to forward messages of any kind. Service messages can't be forwarded. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#forwardmessage
    """

    __returning__ = Message
    __api_method__ = "forwardMessage"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    from_chat_id: Union[int, str]
    """Unique identifier for the chat where the original message was sent (or channel username in the format :code:`@channelusername`)"""
    message_id: int
    """Message identifier in the chat specified in *from_chat_id*"""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[bool] = UNSET_PROTECT_CONTENT
    """Protects the contents of the forwarded message from forwarding and saving"""
