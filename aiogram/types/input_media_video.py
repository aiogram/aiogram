from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from ..client.default import Default
from ..enums import InputMediaType
from .input_media import InputMedia

if TYPE_CHECKING:
    from .input_file import InputFile
    from .message_entity import MessageEntity


class InputMediaVideo(InputMedia):
    """
    Represents a video to be sent.

    Source: https://core.telegram.org/bots/api#inputmediavideo
    """

    type: Literal[InputMediaType.VIDEO] = InputMediaType.VIDEO
    """Type of the result, must be *video*"""
    media: Union[str, InputFile]
    """File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. :ref:`More information on Sending Files » <sending-files>`"""
    thumbnail: Optional[InputFile] = None
    """*Optional*. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`"""
    cover: Optional[Union[str, InputFile]] = None
    """*Optional*. Cover for the video in the message. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. :ref:`More information on Sending Files » <sending-files>`"""
    start_timestamp: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None
    """*Optional*. Start timestamp for the video in the message"""
    caption: Optional[str] = None
    """*Optional*. Caption of the video to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[Union[str, Default]] = Default("parse_mode")
    """*Optional*. Mode for parsing entities in the video caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[list[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    show_caption_above_media: Optional[Union[bool, Default]] = Default("show_caption_above_media")
    """*Optional*. Pass :code:`True`, if the caption must be shown above the message media"""
    width: Optional[int] = None
    """*Optional*. Video width"""
    height: Optional[int] = None
    """*Optional*. Video height"""
    duration: Optional[int] = None
    """*Optional*. Video duration in seconds"""
    supports_streaming: Optional[bool] = None
    """*Optional*. Pass :code:`True` if the uploaded video is suitable for streaming"""
    has_spoiler: Optional[bool] = None
    """*Optional*. Pass :code:`True` if the video needs to be covered with a spoiler animation"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputMediaType.VIDEO] = InputMediaType.VIDEO,
            media: Union[str, InputFile],
            thumbnail: Optional[InputFile] = None,
            cover: Optional[Union[str, InputFile]] = None,
            start_timestamp: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
            caption: Optional[str] = None,
            parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
            caption_entities: Optional[list[MessageEntity]] = None,
            show_caption_above_media: Optional[Union[bool, Default]] = Default(
                "show_caption_above_media"
            ),
            width: Optional[int] = None,
            height: Optional[int] = None,
            duration: Optional[int] = None,
            supports_streaming: Optional[bool] = None,
            has_spoiler: Optional[bool] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                media=media,
                thumbnail=thumbnail,
                cover=cover,
                start_timestamp=start_timestamp,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                show_caption_above_media=show_caption_above_media,
                width=width,
                height=height,
                duration=duration,
                supports_streaming=supports_streaming,
                has_spoiler=has_spoiler,
                **__pydantic_kwargs,
            )
