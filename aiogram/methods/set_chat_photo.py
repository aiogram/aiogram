from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Union

from ..types import InputFile
from .base import Request, TelegramMethod, prepare_file

if TYPE_CHECKING:
    from ..client.bot import Bot


class SetChatPhoto(TelegramMethod[bool]):
    """
    Use this method to set a new profile photo for the chat. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setchatphoto
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    photo: InputFile
    """New chat photo, uploaded using multipart/form-data"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict(exclude={"photo"})

        files: Dict[str, InputFile] = {}
        prepare_file(data=data, files=files, name="photo", value=self.photo)

        return Request(method="setChatPhoto", data=data, files=files)
