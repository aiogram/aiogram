from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import Field

from ..client.default import Default
from ..types import (
    ChatIdUnion,
    InputFile,
    InputFileUnion,
    Message,
    ReplyMarkupUnion,
    ReplyParameters,
)
from .base import TelegramMethod


class SendVideoNote(TelegramMethod[Message]):
    """
    As of `v.4.0 <https://telegram.org/blog/video-messages-and-telescope>`_, Telegram clients support rounded square MPEG4 videos of up to 1 minute long. Use this method to send video messages. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#sendvideonote
    """

    __returning__ = Message
    __api_method__ = "sendVideoNote"

    chat_id: ChatIdUnion
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    video_note: InputFileUnion
    """Video note to send. Pass a file_id as String to send a video note that exists on the Telegram servers (recommended) or upload a new video using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`. Sending video notes by a URL is currently unsupported"""
    business_connection_id: Optional[str] = None
    """Unique identifier of the business connection on behalf of which the message will be sent"""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    duration: Optional[int] = None
    """Duration of sent video in seconds"""
    length: Optional[int] = None
    """Video width and height, i.e. diameter of the video message"""
    thumbnail: Optional[InputFile] = None
    """Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`"""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[Union[bool, Default]] = Default("protect_content")
    """Protects the contents of the sent message from forwarding and saving"""
    allow_paid_broadcast: Optional[bool] = None
    """Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance"""
    message_effect_id: Optional[str] = None
    """Unique identifier of the message effect to be added to the message; for private chats only"""
    reply_parameters: Optional[ReplyParameters] = None
    """Description of the message to reply to"""
    reply_markup: Optional[ReplyMarkupUnion] = None
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
            chat_id: ChatIdUnion,
            video_note: InputFileUnion,
            business_connection_id: Optional[str] = None,
            message_thread_id: Optional[int] = None,
            duration: Optional[int] = None,
            length: Optional[int] = None,
            thumbnail: Optional[InputFile] = None,
            disable_notification: Optional[bool] = None,
            protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
            allow_paid_broadcast: Optional[bool] = None,
            message_effect_id: Optional[str] = None,
            reply_parameters: Optional[ReplyParameters] = None,
            reply_markup: Optional[ReplyMarkupUnion] = None,
            allow_sending_without_reply: Optional[bool] = None,
            reply_to_message_id: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                video_note=video_note,
                business_connection_id=business_connection_id,
                message_thread_id=message_thread_id,
                duration=duration,
                length=length,
                thumbnail=thumbnail,
                disable_notification=disable_notification,
                protect_content=protect_content,
                allow_paid_broadcast=allow_paid_broadcast,
                message_effect_id=message_effect_id,
                reply_parameters=reply_parameters,
                reply_markup=reply_markup,
                allow_sending_without_reply=allow_sending_without_reply,
                reply_to_message_id=reply_to_message_id,
                **__pydantic_kwargs,
            )
