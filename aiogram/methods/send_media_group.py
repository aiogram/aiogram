from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Union

from pydantic import Field

from ..client.default import Default
from ..types import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
    ReplyParameters,
)
from .base import TelegramMethod


class SendMediaGroup(TelegramMethod[List[Message]]):
    """
    Use this method to send a group of photos, videos, documents or audios as an album. Documents and audio files can be only grouped in an album with messages of the same type. On success, an array of `Messages <https://core.telegram.org/bots/api#message>`_ that were sent is returned.

    Source: https://core.telegram.org/bots/api#sendmediagroup
    """

    __returning__ = List[Message]
    __api_method__ = "sendMediaGroup"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    media: List[Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]]
    """A JSON-serialized array describing messages to be sent, must include 2-10 items"""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    disable_notification: Optional[bool] = None
    """Sends messages `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[Union[bool, Default]] = Default("protect_content")
    """Protects the contents of the sent messages from forwarding and saving"""
    reply_parameters: Optional[ReplyParameters] = None
    """Description of the message to reply to"""
    allow_sending_without_reply: Optional[bool] = Field(
        None, json_schema_extra={"deprecated": True}
    )
    """Pass :code:`True` if the message should be sent even if the specified replied-to message is not found

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""
    reply_to_message_id: Optional[int] = Field(None, json_schema_extra={"deprecated": True})
    """If the messages are a reply, ID of the original message

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: Union[int, str],
            media: List[
                Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]
            ],
            message_thread_id: Optional[int] = None,
            disable_notification: Optional[bool] = None,
            protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
            reply_parameters: Optional[ReplyParameters] = None,
            allow_sending_without_reply: Optional[bool] = None,
            reply_to_message_id: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                media=media,
                message_thread_id=message_thread_id,
                disable_notification=disable_notification,
                protect_content=protect_content,
                reply_parameters=reply_parameters,
                allow_sending_without_reply=allow_sending_without_reply,
                reply_to_message_id=reply_to_message_id,
                **__pydantic_kwargs,
            )
