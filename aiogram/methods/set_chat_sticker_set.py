from __future__ import annotations

from typing import Union

from .base import TelegramMethod


class SetChatStickerSet(TelegramMethod[bool]):
    """
    Use this method to set a new group sticker set for a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field *can_set_sticker_set* optionally returned in :class:`aiogram.methods.get_chat.GetChat` requests to check if the bot can use this method. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setchatstickerset
    """

    __returning__ = bool
    __api_method__ = "setChatStickerSet"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
    sticker_set_name: str
    """Name of the sticker set to be set as the group sticker set"""
