from __future__ import annotations

from typing import Union

from ..types import InputFile
from .base import TelegramMethod


class SetChatPhoto(TelegramMethod[bool]):
    """
    Use this method to set a new profile photo for the chat. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setchatphoto
    """

    __returning__ = bool
    __api_method__ = "setChatPhoto"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    photo: InputFile
    """New chat photo, uploaded using multipart/form-data"""
