from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..types import (
    UNSET,
    ForceReply,
    InlineKeyboardMarkup,
    InputFile,
    Message,
    MessageEntity,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .base import Request, TelegramMethod, prepare_file, prepare_parse_mode

if TYPE_CHECKING:
    from ..client.bot import Bot


class SendVoice(TelegramMethod[Message]):
    """
    Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .OGG file encoded with OPUS (other formats may be sent as :class:`aiogram.types.audio.Audio` or :class:`aiogram.types.document.Document`). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.

    Source: https://core.telegram.org/bots/api#sendvoice
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    voice: Union[InputFile, str]
    """Audio file to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`"""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    caption: Optional[str] = None
    """Voice message caption, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """Mode for parsing entities in the voice message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[List[MessageEntity]] = None
    """A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    duration: Optional[int] = None
    """Duration of the voice message in seconds"""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[bool] = None
    """Protects the contents of the sent message from forwarding and saving"""
    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""
    allow_sending_without_reply: Optional[bool] = None
    """Pass :code:`True` if the message should be sent even if the specified replied-to message is not found"""
    reply_markup: Optional[
        Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
    ] = None
    """Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict(exclude={"voice"})

        prepare_parse_mode(
            bot, data, parse_mode_property="parse_mode", entities_property="caption_entities"
        )

        files: Dict[str, InputFile] = {}
        prepare_file(data=data, files=files, name="voice", value=self.voice)

        return Request(method="sendVoice", data=data, files=files)
