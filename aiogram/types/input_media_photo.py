from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from ..client.default import Default
from ..enums import InputMediaType
from .input_media import InputMedia

if TYPE_CHECKING:
    from .input_file import InputFile
    from .message_entity import MessageEntity


class InputMediaPhoto(InputMedia):
    """
    Represents a photo to be sent.

    Source: https://core.telegram.org/bots/api#inputmediaphoto
    """

    type: Literal[InputMediaType.PHOTO] = InputMediaType.PHOTO
    """Type of the result, must be *photo*"""
    media: Union[str, InputFile]
    """File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. :ref:`More information on Sending Files » <sending-files>`"""
    caption: Optional[str] = None
    """*Optional*. Caption of the photo to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[Union[str, Default]] = Default("parse_mode")
    """*Optional*. Mode for parsing entities in the photo caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[list[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    show_caption_above_media: Optional[Union[bool, Default]] = Default("show_caption_above_media")
    """*Optional*. Pass :code:`True`, if the caption must be shown above the message media"""
    has_spoiler: Optional[bool] = None
    """*Optional*. Pass :code:`True` if the photo needs to be covered with a spoiler animation"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputMediaType.PHOTO] = InputMediaType.PHOTO,
            media: Union[str, InputFile],
            caption: Optional[str] = None,
            parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
            caption_entities: Optional[list[MessageEntity]] = None,
            show_caption_above_media: Optional[Union[bool, Default]] = Default(
                "show_caption_above_media"
            ),
            has_spoiler: Optional[bool] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                media=media,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                show_caption_above_media=show_caption_above_media,
                has_spoiler=has_spoiler,
                **__pydantic_kwargs,
            )
