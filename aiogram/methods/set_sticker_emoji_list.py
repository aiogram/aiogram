from __future__ import annotations

from typing import TYPE_CHECKING, List

from .base import TelegramMethod


class SetStickerEmojiList(TelegramMethod[bool]):
    """
    Use this method to change the list of emoji assigned to a regular or custom emoji sticker. The sticker must belong to a sticker set created by the bot. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setstickeremojilist
    """

    __returning__ = bool
    __api_method__ = "setStickerEmojiList"

    sticker: str
    """File identifier of the sticker"""
    emoji_list: List[str]
    """A JSON-serialized list of 1-20 emoji associated with the sticker"""
