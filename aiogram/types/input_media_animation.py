from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from pydantic import Field

from ..enums import InputMediaType
from .base import UNSET
from .input_media import InputMedia

if TYPE_CHECKING:
    from .input_file import InputFile
    from .message_entity import MessageEntity


class InputMediaAnimation(InputMedia):
    """
    Represents an animation file (GIF or H.264/MPEG-4 AVC video without sound) to be sent.

    Source: https://core.telegram.org/bots/api#inputmediaanimation
    """

    type: str = Field(InputMediaType.ANIMATION, const=True)
    """Type of the result, must be *animation*"""
    media: Union[str, InputFile]
    """File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. :ref:`More information on Sending Files » <sending-files>`"""
    thumb: Optional[Union[InputFile, str]] = None
    """*Optional*. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`"""
    caption: Optional[str] = None
    """*Optional*. Caption of the animation to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """*Optional*. Mode for parsing entities in the animation caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[List[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    width: Optional[int] = None
    """*Optional*. Animation width"""
    height: Optional[int] = None
    """*Optional*. Animation height"""
    duration: Optional[int] = None
    """*Optional*. Animation duration in seconds"""
    has_spoiler: Optional[bool] = None
    """*Optional*. Pass :code:`True` if the animation needs to be covered with a spoiler animation"""
