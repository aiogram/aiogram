from __future__ import annotations

from typing import Optional

from pydantic import Field

from .input_media import InputMedia


class InputMediaPhoto(InputMedia):
    """
    Represents a photo to be sent.

    Source: https://core.telegram.org/bots/api#inputmediaphoto
    """

    type: str = Field("photo", const=True)
    """Type of the result, must be photo"""
    media: str
    """File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name."""
    caption: Optional[str] = None
    """Caption of the photo to be sent, 0-1024 characters"""
    parse_mode: Optional[str] = None
    """Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption."""
