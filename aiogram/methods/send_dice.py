from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from ..types.base import UNSET_PROTECT_CONTENT
from .base import TelegramMethod


class SendDice(TelegramMethod[Message]):
    """
    Use this method to send an animated emoji that will display a random value. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#senddice
    """

    __returning__ = Message
    __api_method__ = "sendDice"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    emoji: Optional[str] = None
    """Emoji on which the dice throw animation is based. Currently, must be one of '🎲', '🎯', '🏀', '⚽', '🎳', or '🎰'. Dice can have values 1-6 for '🎲', '🎯' and '🎳', values 1-5 for '🏀' and '⚽', and values 1-64 for '🎰'. Defaults to '🎲'"""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[bool] = UNSET_PROTECT_CONTENT
    """Protects the contents of the sent message from forwarding"""
    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""
    allow_sending_without_reply: Optional[bool] = None
    """Pass :code:`True` if the message should be sent even if the specified replied-to message is not found"""
    reply_markup: Optional[
        Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
    ] = None
    """Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: Union[int, str],
            message_thread_id: Optional[int] = None,
            emoji: Optional[str] = None,
            disable_notification: Optional[bool] = None,
            protect_content: Optional[bool] = UNSET_PROTECT_CONTENT,
            reply_to_message_id: Optional[int] = None,
            allow_sending_without_reply: Optional[bool] = None,
            reply_markup: Optional[
                Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
            ] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
                emoji=emoji,
                disable_notification=disable_notification,
                protect_content=protect_content,
                reply_to_message_id=reply_to_message_id,
                allow_sending_without_reply=allow_sending_without_reply,
                reply_markup=reply_markup,
                **__pydantic_kwargs,
            )
