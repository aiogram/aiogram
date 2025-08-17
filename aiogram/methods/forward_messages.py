from typing import TYPE_CHECKING, Any, Optional

from ..types import ChatIdUnion, MessageId
from .base import TelegramMethod


class ForwardMessages(TelegramMethod[list[MessageId]]):
    """
    Use this method to forward multiple messages of any kind. If some of the specified messages can't be found or forwarded, they are skipped. Service messages and messages with protected content can't be forwarded. Album grouping is kept for forwarded messages. On success, an array of :class:`aiogram.types.message_id.MessageId` of the sent messages is returned.

    Source: https://core.telegram.org/bots/api#forwardmessages
    """

    __returning__ = list[MessageId]
    __api_method__ = "forwardMessages"

    chat_id: ChatIdUnion
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    from_chat_id: ChatIdUnion
    """Unique identifier for the chat where the original messages were sent (or channel username in the format :code:`@channelusername`)"""
    message_ids: list[int]
    """A JSON-serialized list of 1-100 identifiers of messages in the chat *from_chat_id* to forward. The identifiers must be specified in a strictly increasing order."""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    direct_messages_topic_id: Optional[int] = None
    """Identifier of the direct messages topic to which the messages will be forwarded; required if the messages are forwarded to a direct messages chat"""
    disable_notification: Optional[bool] = None
    """Sends the messages `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[bool] = None
    """Protects the contents of the forwarded messages from forwarding and saving"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: ChatIdUnion,
            from_chat_id: ChatIdUnion,
            message_ids: list[int],
            message_thread_id: Optional[int] = None,
            direct_messages_topic_id: Optional[int] = None,
            disable_notification: Optional[bool] = None,
            protect_content: Optional[bool] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                from_chat_id=from_chat_id,
                message_ids=message_ids,
                message_thread_id=message_thread_id,
                direct_messages_topic_id=direct_messages_topic_id,
                disable_notification=disable_notification,
                protect_content=protect_content,
                **__pydantic_kwargs,
            )
