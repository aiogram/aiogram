from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import InputRichBlockType
from .base import TelegramObject
from .input_rich_block import InputRichBlock

if TYPE_CHECKING:
    from .input_media_voice_note import InputMediaVoiceNote
    from .rich_block_caption import RichBlockCaption


class InputRichBlockVoiceNote(InputRichBlock):
    """
    A block with a voice note, corresponding to the HTML tag :code:`<audio>`.

    Source: https://core.telegram.org/bots/api#inputrichblockvoicenote
    """

    type: Literal[InputRichBlockType.VOICE_NOTE] = InputRichBlockType.VOICE_NOTE
    """Type of the block, always 'voice_note'"""
    voice_note: InputMediaVoiceNote
    """The voice note. Caption is ignored"""
    caption: RichBlockCaption | None = None
    """*Optional*. Caption of the block"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputRichBlockType.VOICE_NOTE] = InputRichBlockType.VOICE_NOTE,
            voice_note: InputMediaVoiceNote,
            caption: RichBlockCaption | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type, voice_note=voice_note, caption=caption, **__pydantic_kwargs
            )
