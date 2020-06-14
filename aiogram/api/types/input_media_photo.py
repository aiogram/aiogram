from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from pydantic import Field

from .base import UNSET
from .input_media import InputMedia

if TYPE_CHECKING:  # pragma: no cover
    from .input_file import InputFile


class InputMediaPhoto(InputMedia):
    """
    Represents a photo to be sent.

    Source: https://core.telegram.org/bots/api#inputmediaphoto
    """

    type: str = Field("photo", const=True)
    """Type of the result, must be photo"""
    media: Union[str, InputFile]
    """File to send. Pass a file_id to send a file that exists on the Telegram servers
    (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass
    'attach://<file_attach_name>' to upload a new one using multipart/form-data under
    <file_attach_name> name."""
    caption: Optional[str] = None
    """Caption of the photo to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or
    inline URLs in the media caption."""
