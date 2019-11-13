from typing import Any, Dict, Union

from .base import Request, TelegramMethod


class DeleteChatStickerSet(TelegramMethod[bool]):
    """
    Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success.

    Source: https://core.telegram.org/bots/api#deletechatstickerset
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})

        return Request(method="deleteChatStickerSet", data=data)
