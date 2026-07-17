from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from .base import TelegramObject

if TYPE_CHECKING:
    from .message_entity import MessageEntity


class InputMediaVoiceNote(TelegramObject):
    """
    Represents a voice message file to be sent.

    Source: https://core.telegram.org/bots/api#inputmediavoicenote
    """

    type: Literal["voice_note"] = "voice_note"
    """Type of the media, must be *voice_note*"""
    media: str
    """File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass "attach://<file_attach_name>" to upload a new one using multipart/form-data under <file_attach_name> name. :ref:`More information on Sending Files » <sending-files>`"""
    caption: str | None = None
    """*Optional*. Caption of the voice message to be sent, 0-1024 characters after entities parsing"""
    parse_mode: str | None = None
    """*Optional*. Mode for parsing entities in the voice message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details"""
    caption_entities: list[MessageEntity] | None = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    duration: int | None = None
    """*Optional*. Duration of the voice message in seconds"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal["voice_note"] = "voice_note",
            media: str,
            caption: str | None = None,
            parse_mode: str | None = None,
            caption_entities: list[MessageEntity] | None = None,
            duration: int | None = None,
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
                duration=duration,
                **__pydantic_kwargs,
            )
