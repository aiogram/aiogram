from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import Field

from ..client.default import Default
from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ReplyParameters,
)
from .base import TelegramMethod


class SendContact(TelegramMethod[Message]):
    """
    Use this method to send phone contacts. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#sendcontact
    """

    __returning__ = Message
    __api_method__ = "sendContact"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    phone_number: str
    """Contact's phone number"""
    first_name: str
    """Contact's first name"""
    business_connection_id: Optional[str] = None
    """Unique identifier of the business connection on behalf of which the message will be sent"""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    last_name: Optional[str] = None
    """Contact's last name"""
    vcard: Optional[str] = None
    """Additional data about the contact in the form of a `vCard <https://en.wikipedia.org/wiki/VCard>`_, 0-2048 bytes"""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[Union[bool, Default]] = Default("protect_content")
    """Protects the contents of the sent message from forwarding and saving"""
    reply_parameters: Optional[ReplyParameters] = None
    """Description of the message to reply to"""
    reply_markup: Optional[
        Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
    ] = None
    """Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user"""
    allow_sending_without_reply: Optional[bool] = Field(
        None, json_schema_extra={"deprecated": True}
    )
    """Pass :code:`True` if the message should be sent even if the specified replied-to message is not found

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""
    reply_to_message_id: Optional[int] = Field(None, json_schema_extra={"deprecated": True})
    """If the message is a reply, ID of the original message

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: Union[int, str],
            phone_number: str,
            first_name: str,
            business_connection_id: Optional[str] = None,
            message_thread_id: Optional[int] = None,
            last_name: Optional[str] = None,
            vcard: Optional[str] = None,
            disable_notification: Optional[bool] = None,
            protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
            reply_parameters: Optional[ReplyParameters] = None,
            reply_markup: Optional[
                Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
            ] = None,
            allow_sending_without_reply: Optional[bool] = None,
            reply_to_message_id: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                phone_number=phone_number,
                first_name=first_name,
                business_connection_id=business_connection_id,
                message_thread_id=message_thread_id,
                last_name=last_name,
                vcard=vcard,
                disable_notification=disable_notification,
                protect_content=protect_content,
                reply_parameters=reply_parameters,
                reply_markup=reply_markup,
                allow_sending_without_reply=allow_sending_without_reply,
                reply_to_message_id=reply_to_message_id,
                **__pydantic_kwargs,
            )
