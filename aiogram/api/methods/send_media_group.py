from typing import Any, Dict, List, Optional, Union

from ..types import InputFile, InputMediaPhoto, InputMediaVideo, Message
from .base import Request, TelegramMethod, prepare_input_media, prepare_parse_mode


class SendMediaGroup(TelegramMethod[List[Message]]):
    """
    Use this method to send a group of photos or videos as an album. On success, an array of the
    sent Messages is returned.

    Source: https://core.telegram.org/bots/api#sendmediagroup
    """

    __returning__ = List[Message]

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format
    @channelusername)"""
    media: List[Union[InputMediaPhoto, InputMediaVideo]]
    """A JSON-serialized array describing photos and videos to be sent, must include 2-10 items"""
    disable_notification: Optional[bool] = None
    """Sends the messages silently. Users will receive a notification with no sound."""
    reply_to_message_id: Optional[int] = None
    """If the messages are a reply, ID of the original message"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()
        prepare_parse_mode(data["media"])

        files: Dict[str, InputFile] = {}
        prepare_input_media(data, files)

        return Request(method="sendMediaGroup", data=data, files=files)
