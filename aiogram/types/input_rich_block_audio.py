from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import InputRichBlockType
from .base import TelegramObject
from .input_rich_block import InputRichBlock

if TYPE_CHECKING:
    from .input_media_audio import InputMediaAudio
    from .rich_block_caption import RichBlockCaption


class InputRichBlockAudio(InputRichBlock):
    """
    A block with a music file, corresponding to the HTML tag :code:`<audio>`.

    Source: https://core.telegram.org/bots/api#inputrichblockaudio
    """

    type: Literal[InputRichBlockType.AUDIO] = InputRichBlockType.AUDIO
    """Type of the block, always 'audio'"""
    audio: InputMediaAudio
    """The audio. Caption is ignored"""
    caption: RichBlockCaption | None = None
    """*Optional*. Caption of the block"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputRichBlockType.AUDIO] = InputRichBlockType.AUDIO,
            audio: InputMediaAudio,
            caption: RichBlockCaption | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, audio=audio, caption=caption, **__pydantic_kwargs)
