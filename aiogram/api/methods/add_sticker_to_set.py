from typing import Any, Dict, Optional, Union

from ..types import InputFile, MaskPosition
from .base import Request, TelegramMethod


class AddStickerToSet(TelegramMethod[bool]):
    """
    Use this method to add a new sticker to a set created by the bot. Returns True on success.

    Source: https://core.telegram.org/bots/api#addstickertoset
    """

    __returning__ = bool

    user_id: int
    """User identifier of sticker set owner"""

    name: str
    """Sticker set name"""

    png_sticker: Union[InputFile, str]
    """Png image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a file_id as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data."""

    emojis: str
    """One or more emoji corresponding to the sticker"""

    mask_position: Optional[MaskPosition] = None
    """A JSON-serialized object for position where the mask should be placed on faces"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(
            exclude={"png_sticker",}
        )

        files: Dict[str, InputFile] = {}
        self.prepare_file(data=data, files=files, name="png_sticker", value=self.png_sticker)

        return Request(method="addStickerToSet", data=data, files=files)
