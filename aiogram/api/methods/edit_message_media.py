from typing import Any, Dict, Optional, Union

from ..types import InlineKeyboardMarkup, InputFile, Message
from .base import Request, TelegramMethod


class EditMessageMedia(TelegramMethod[Union[Message, bool]]):
    """
    Use this method to edit animation, audio, document, photo, or video messages. If a message is a part of a message album, then it can be edited only to a photo or a video. Otherwise, message type can be changed arbitrarily. When inline message is edited, new file can't be uploaded. Use previously uploaded file via its file_id or specify a URL. On success, if the edited message was sent by the bot, the edited Message is returned, otherwise True is returned.

    Source: https://core.telegram.org/bots/api#editmessagemedia
    """

    __returning__ = Union[Message, bool]

    media: Union[str, InputFile]
    """A JSON-serialized object for a new media content of the message"""

    chat_id: Optional[Union[int, str]] = None
    """Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername)"""

    message_id: Optional[int] = None
    """Required if inline_message_id is not specified. Identifier of the message to edit"""

    inline_message_id: Optional[str] = None
    """Required if chat_id and message_id are not specified. Identifier of the inline message"""

    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for a new inline keyboard."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(
            exclude={"media",}
        )

        files: Dict[str, InputFile] = {}
        self.prepare_file(data=data, files=files, name="media", value=self.media)

        return Request(method="editMessageMedia", data=data, files=files)
