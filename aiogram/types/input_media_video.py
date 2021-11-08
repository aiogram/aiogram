from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from pydantic import Field

from .base import UNSET
from .input_media import InputMedia

if TYPE_CHECKING:
    from .input_file import InputFile
    from .message_entity import MessageEntity


class InputMediaVideo(InputMedia):
    """
    Represents a video to be sent.

    Source: https://core.telegram.org/bots/api#inputmediavideo
    """

    type: str = Field("video", const=True)
    """Type of the result, must be *video*"""
    media: Union[str, InputFile]
    """File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. :ref:`More info on Sending Files » <sending-files>`"""
    thumb: Optional[Union[InputFile, str]] = None
    """*Optional*. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More info on Sending Files » <sending-files>`"""
    caption: Optional[str] = None
    """*Optional*. Caption of the video to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """*Optional*. Mode for parsing entities in the video caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[List[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    width: Optional[int] = None
    """*Optional*. Video width"""
    height: Optional[int] = None
    """*Optional*. Video height"""
    duration: Optional[int] = None
    """*Optional*. Video duration in seconds"""
    supports_streaming: Optional[bool] = None
    """*Optional*. Pass :code:`True`, if the uploaded video is suitable for streaming"""
