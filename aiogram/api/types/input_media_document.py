from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from pydantic import Field

from .input_media import InputMedia

if TYPE_CHECKING:
    from .input_file import InputFile


class InputMediaDocument(InputMedia):
    """
    Represents a general file to be sent.

    Source: https://core.telegram.org/bots/api#inputmediadocument
    """

    type: str = Field("document", const=True)
    """Type of the result, must be document"""
    media: Union[str, InputFile]
    """File to send. Pass a file_id to send a file that exists on the Telegram servers
    (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass
    'attach://<file_attach_name>' to upload a new one using multipart/form-data under
    <file_attach_name> name."""
    thumb: Optional[Union[InputFile, str]] = None
    """Thumbnail of the file sent; can be ignored if thumbnail generation for the file is
    supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size.
    A thumbnail‘s width and height should not exceed 320. Ignored if the file is not uploaded
    using multipart/form-data. Thumbnails can’t be reused and can be only uploaded as a new
    file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using
    multipart/form-data under <file_attach_name>."""
    caption: Optional[str] = None
    """Caption of the document to be sent, 0-1024 characters"""
    parse_mode: Optional[str] = None
    """Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or
    inline URLs in the media caption."""
