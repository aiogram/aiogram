from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..types import (
    InputFile,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)
from .base import Request, TelegramMethod, prepare_input_media, prepare_parse_mode

if TYPE_CHECKING:
    from ..client.bot import Bot


class SendMediaGroup(TelegramMethod[List[Message]]):
    """
    Use this method to send a group of photos, videos, documents or audios as an album. Documents and audio files can be only grouped in an album with messages of the same type. On success, an array of `Messages <https://core.telegram.org/bots/api#message>`_ that were sent is returned.

    Source: https://core.telegram.org/bots/api#sendmediagroup
    """

    __returning__ = List[Message]

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    media: List[Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]]
    """A JSON-serialized array describing messages to be sent, must include 2-10 items"""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    disable_notification: Optional[bool] = None
    """Sends messages `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[bool] = None
    """Protects the contents of the sent messages from forwarding and saving"""
    reply_to_message_id: Optional[int] = None
    """If the messages are a reply, ID of the original message"""
    allow_sending_without_reply: Optional[bool] = None
    """Pass :code:`True` if the message should be sent even if the specified replied-to message is not found"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()
        prepare_parse_mode(bot, data["media"])

        files: Dict[str, InputFile] = {}
        prepare_input_media(data, files)

        return Request(method="sendMediaGroup", data=data, files=files)
