from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from ..client.default import Default
from ..types import ChatIdUnion, DateTimeUnion, Message, SuggestedPostParameters
from .base import TelegramMethod


class ForwardMessage(TelegramMethod[Message]):
    """
    Use this method to forward messages of any kind. Service messages and messages with protected content can't be forwarded. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#forwardmessage
    """

    __returning__ = Message
    __api_method__ = "forwardMessage"

    chat_id: ChatIdUnion
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    from_chat_id: ChatIdUnion
    """Unique identifier for the chat where the original message was sent (or channel username in the format :code:`@channelusername`)"""
    message_id: int
    """Message identifier in the chat specified in *from_chat_id*"""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    direct_messages_topic_id: Optional[int] = None
    """Identifier of the direct messages topic to which the message will be forwarded; required if the message is forwarded to a direct messages chat"""
    video_start_timestamp: Optional[DateTimeUnion] = None
    """New start timestamp for the forwarded video in the message"""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[Union[bool, Default]] = Default("protect_content")
    """Protects the contents of the forwarded message from forwarding and saving"""
    suggested_post_parameters: Optional[SuggestedPostParameters] = None
    """A JSON-serialized object containing the parameters of the suggested post to send; for direct messages chats only"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: ChatIdUnion,
            from_chat_id: ChatIdUnion,
            message_id: int,
            message_thread_id: Optional[int] = None,
            direct_messages_topic_id: Optional[int] = None,
            video_start_timestamp: Optional[DateTimeUnion] = None,
            disable_notification: Optional[bool] = None,
            protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
            suggested_post_parameters: Optional[SuggestedPostParameters] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
                message_thread_id=message_thread_id,
                direct_messages_topic_id=direct_messages_topic_id,
                video_start_timestamp=video_start_timestamp,
                disable_notification=disable_notification,
                protect_content=protect_content,
                suggested_post_parameters=suggested_post_parameters,
                **__pydantic_kwargs,
            )
