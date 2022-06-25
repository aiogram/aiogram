from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from pydantic import Field

from .base import UNSET
from .input_media import InputMedia

if TYPE_CHECKING:
    from .input_file import InputFile
    from .message_entity import MessageEntity


class InputMediaPhoto(InputMedia):
    """
    Represents a photo to be sent.

    Source: https://core.telegram.org/bots/api#inputmediaphoto
    """

    type: str = Field("photo", const=True)
    """Type of the result, must be *photo*"""
    media: Union[str, InputFile]
    """File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. :ref:`More information on Sending Files » <sending-files>`"""
    caption: Optional[str] = None
    """*Optional*. Caption of the photo to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """*Optional*. Mode for parsing entities in the photo caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[List[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
