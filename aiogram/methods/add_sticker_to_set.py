from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import InputFile, MaskPosition
from .base import Request, TelegramMethod, prepare_file

if TYPE_CHECKING:
    from ..client.bot import Bot


class AddStickerToSet(TelegramMethod[bool]):
    """
    Use this method to add a new sticker to a set created by the bot. You **must** use exactly one of the fields *png_sticker*, *tgs_sticker*, or *webm_sticker*. Animated stickers can be added to animated sticker sets and only to them. Animated sticker sets can have up to 50 stickers. Static sticker sets can have up to 120 stickers. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#addstickertoset
    """

    __returning__ = bool

    user_id: int
    """User identifier of sticker set owner"""
    name: str
    """Sticker set name"""
    emojis: str
    """One or more emoji corresponding to the sticker"""
    png_sticker: Optional[Union[InputFile, str]] = None
    """**PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`"""
    tgs_sticker: Optional[InputFile] = None
    """**TGS** animation with the sticker, uploaded using multipart/form-data. See `https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_`https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_ for technical requirements"""
    webm_sticker: Optional[InputFile] = None
    """**WEBM** video with the sticker, uploaded using multipart/form-data. See `https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_`https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_ for technical requirements"""
    mask_position: Optional[MaskPosition] = None
    """A JSON-serialized object for position where the mask should be placed on faces"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict(exclude={"png_sticker", "tgs_sticker", "webm_sticker"})

        files: Dict[str, InputFile] = {}
        prepare_file(data=data, files=files, name="png_sticker", value=self.png_sticker)
        prepare_file(data=data, files=files, name="tgs_sticker", value=self.tgs_sticker)
        prepare_file(data=data, files=files, name="webm_sticker", value=self.webm_sticker)

        return Request(method="addStickerToSet", data=data, files=files)
