from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from ..client.default import Default
from ..enums import InputMediaType
from .input_media import InputMedia

if TYPE_CHECKING:
    from .input_file import InputFile
    from .message_entity import MessageEntity


class InputMediaAudio(InputMedia):
    """
    Represents an audio file to be treated as music to be sent.

    Source: https://core.telegram.org/bots/api#inputmediaaudio
    """

    type: Literal[InputMediaType.AUDIO] = InputMediaType.AUDIO
    """Type of the result, must be *audio*"""
    media: Union[str, InputFile]
    """File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. :ref:`More information on Sending Files » <sending-files>`"""
    thumbnail: Optional[InputFile] = None
    """*Optional*. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`"""
    caption: Optional[str] = None
    """*Optional*. Caption of the audio to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[Union[str, Default]] = Default("parse_mode")
    """*Optional*. Mode for parsing entities in the audio caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[list[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    duration: Optional[int] = None
    """*Optional*. Duration of the audio in seconds"""
    performer: Optional[str] = None
    """*Optional*. Performer of the audio"""
    title: Optional[str] = None
    """*Optional*. Title of the audio"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputMediaType.AUDIO] = InputMediaType.AUDIO,
            media: Union[str, InputFile],
            thumbnail: Optional[InputFile] = None,
            caption: Optional[str] = None,
            parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
            caption_entities: Optional[list[MessageEntity]] = None,
            duration: Optional[int] = None,
            performer: Optional[str] = None,
            title: Optional[str] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                media=media,
                thumbnail=thumbnail,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                duration=duration,
                performer=performer,
                title=title,
                **__pydantic_kwargs,
            )
