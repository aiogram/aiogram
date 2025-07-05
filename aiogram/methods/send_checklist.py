from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ..types import InlineKeyboardMarkup, InputChecklist, Message, ReplyParameters
from .base import TelegramMethod


class SendChecklist(TelegramMethod[Message]):
    """
    Use this method to send a checklist on behalf of a connected business account. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#sendchecklist
    """

    __returning__ = Message
    __api_method__ = "sendChecklist"

    business_connection_id: str
    """Unique identifier of the business connection on behalf of which the message will be sent"""
    chat_id: int
    """Unique identifier for the target chat"""
    checklist: InputChecklist
    """A JSON-serialized object for the checklist to send"""
    disable_notification: Optional[bool] = None
    """Sends the message silently. Users will receive a notification with no sound."""
    protect_content: Optional[bool] = None
    """Protects the contents of the sent message from forwarding and saving"""
    message_effect_id: Optional[str] = None
    """Unique identifier of the message effect to be added to the message"""
    reply_parameters: Optional[ReplyParameters] = None
    """A JSON-serialized object for description of the message to reply to"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for an inline keyboard"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            business_connection_id: str,
            chat_id: int,
            checklist: InputChecklist,
            disable_notification: Optional[bool] = None,
            protect_content: Optional[bool] = None,
            message_effect_id: Optional[str] = None,
            reply_parameters: Optional[ReplyParameters] = None,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                business_connection_id=business_connection_id,
                chat_id=chat_id,
                checklist=checklist,
                disable_notification=disable_notification,
                protect_content=protect_content,
                message_effect_id=message_effect_id,
                reply_parameters=reply_parameters,
                reply_markup=reply_markup,
                **__pydantic_kwargs,
            )
