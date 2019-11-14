from typing import Any, Dict, Optional, Union

from ..types import InputFile, MaskPosition
from .base import Request, TelegramMethod


class CreateNewStickerSet(TelegramMethod[bool]):
    """
    Use this method to create new sticker set owned by a user. The bot will be able to edit the
    created sticker set. Returns True on success.

    Source: https://core.telegram.org/bots/api#createnewstickerset
    """

    __returning__ = bool

    user_id: int
    """User identifier of created sticker set owner"""
    name: str
    """Short name of sticker set, to be used in t.me/addstickers/ URLs (e.g., animals). Can
    contain only english letters, digits and underscores. Must begin with a letter, can't
    contain consecutive underscores and must end in '_by_<bot username>'. <bot_username> is
    case insensitive. 1-64 characters."""
    title: str
    """Sticker set title, 1-64 characters"""
    png_sticker: Union[InputFile, str]
    """Png image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed
    512px, and either width or height must be exactly 512px. Pass a file_id as a String to send
    a file that already exists on the Telegram servers, pass an HTTP URL as a String for
    Telegram to get a file from the Internet, or upload a new one using multipart/form-data."""
    emojis: str
    """One or more emoji corresponding to the sticker"""
    contains_masks: Optional[bool] = None
    """Pass True, if a set of mask stickers should be created"""
    mask_position: Optional[MaskPosition] = None
    """A JSON-serialized object for position where the mask should be placed on faces"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(
            exclude={"png_sticker",}
        )

        files: Dict[str, InputFile] = {}
        self.prepare_file(data=data, files=files, name="png_sticker", value=self.png_sticker)

        return Request(method="createNewStickerSet", data=data, files=files)
