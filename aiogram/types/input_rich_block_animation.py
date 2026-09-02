from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import InputRichBlockType
from .base import TelegramObject
from .input_rich_block import InputRichBlock

if TYPE_CHECKING:
    from .input_media_animation import InputMediaAnimation
    from .rich_block_caption import RichBlockCaption


class InputRichBlockAnimation(InputRichBlock):
    """
    A block with an animation, corresponding to the HTML tag :code:`<video>`.

    Source: https://core.telegram.org/bots/api#inputrichblockanimation
    """

    type: Literal[InputRichBlockType.ANIMATION] = InputRichBlockType.ANIMATION
    """Type of the block, always 'animation'"""
    animation: InputMediaAnimation
    """The animation. Caption is ignored"""
    caption: RichBlockCaption | None = None
    """*Optional*. Caption of the block"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputRichBlockType.ANIMATION] = InputRichBlockType.ANIMATION,
            animation: InputMediaAnimation,
            caption: RichBlockCaption | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, animation=animation, caption=caption, **__pydantic_kwargs)
