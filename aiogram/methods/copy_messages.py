from typing import TYPE_CHECKING, Any, Optional, Union

from ..types import MessageId
from .base import TelegramMethod


class CopyMessages(TelegramMethod[list[MessageId]]):
    """
    Use this method to copy messages of any kind. If some of the specified messages can't be found or copied, they are skipped. Service messages, paid media messages, giveaway messages, giveaway winners messages, and invoice messages can't be copied. A quiz :class:`aiogram.methods.poll.Poll` can be copied only if the value of the field *correct_option_id* is known to the bot. The method is analogous to the method :class:`aiogram.methods.forward_messages.ForwardMessages`, but the copied messages don't have a link to the original message. Album grouping is kept for copied messages. On success, an array of :class:`aiogram.types.message_id.MessageId` of the sent messages is returned.

    Source: https://core.telegram.org/bots/api#copymessages
    """

    __returning__ = list[MessageId]
    __api_method__ = "copyMessages"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    from_chat_id: Union[int, str]
    """Unique identifier for the chat where the original messages were sent (or channel username in the format :code:`@channelusername`)"""
    message_ids: list[int]
    """A JSON-serialized list of 1-100 identifiers of messages in the chat *from_chat_id* to copy. The identifiers must be specified in a strictly increasing order."""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    disable_notification: Optional[bool] = None
    """Sends the messages `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[bool] = None
    """Protects the contents of the sent messages from forwarding and saving"""
    remove_caption: Optional[bool] = None
    """Pass :code:`True` to copy the messages without their captions"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: Union[int, str],
            from_chat_id: Union[int, str],
            message_ids: list[int],
            message_thread_id: Optional[int] = None,
            disable_notification: Optional[bool] = None,
            protect_content: Optional[bool] = None,
            remove_caption: Optional[bool] = None,
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
                disable_notification=disable_notification,
                protect_content=protect_content,
                remove_caption=remove_caption,
                **__pydantic_kwargs,
            )
