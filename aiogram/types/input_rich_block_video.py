from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import InputRichBlockType
from .base import TelegramObject
from .input_rich_block import InputRichBlock

if TYPE_CHECKING:
    from .input_media_video import InputMediaVideo
    from .rich_block_caption import RichBlockCaption


class InputRichBlockVideo(InputRichBlock):
    """
    A block with a video, corresponding to the HTML tag :code:`<video>`.

    Source: https://core.telegram.org/bots/api#inputrichblockvideo
    """

    type: Literal[InputRichBlockType.VIDEO] = InputRichBlockType.VIDEO
    """Type of the block, always 'video'"""
    video: InputMediaVideo
    """The video. Caption is ignored"""
    caption: RichBlockCaption | None = None
    """*Optional*. Caption of the block"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputRichBlockType.VIDEO] = InputRichBlockType.VIDEO,
            video: InputMediaVideo,
            caption: RichBlockCaption | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, video=video, caption=caption, **__pydantic_kwargs)
