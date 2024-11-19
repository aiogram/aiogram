from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from ..enums import InputPaidMediaType
from .input_file import InputFile
from .input_paid_media import InputPaidMedia


class InputPaidMediaVideo(InputPaidMedia):
    """
    The paid media to send is a video.

    Source: https://core.telegram.org/bots/api#inputpaidmediavideo
    """

    type: Literal[InputPaidMediaType.VIDEO] = InputPaidMediaType.VIDEO
    """Type of the media, must be *video*"""
    media: Union[str, InputFile]
    """File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. :ref:`More information on Sending Files » <sending-files>`"""
    thumbnail: Optional[Union[InputFile, str]] = None
    """*Optional*. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`"""
    width: Optional[int] = None
    """*Optional*. Video width"""
    height: Optional[int] = None
    """*Optional*. Video height"""
    duration: Optional[int] = None
    """*Optional*. Video duration in seconds"""
    supports_streaming: Optional[bool] = None
    """*Optional*. Pass :code:`True` if the uploaded video is suitable for streaming"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputPaidMediaType.VIDEO] = InputPaidMediaType.VIDEO,
            media: Union[str, InputFile],
            thumbnail: Optional[Union[InputFile, str]] = None,
            width: Optional[int] = None,
            height: Optional[int] = None,
            duration: Optional[int] = None,
            supports_streaming: Optional[bool] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                media=media,
                thumbnail=thumbnail,
                width=width,
                height=height,
                duration=duration,
                supports_streaming=supports_streaming,
                **__pydantic_kwargs,
            )
