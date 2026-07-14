from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import InputRichBlockType
from .base import TelegramObject
from .input_rich_block import InputRichBlock

if TYPE_CHECKING:
    from .input_rich_block import InputRichBlock
    from .input_rich_block_union import InputRichBlockUnion
    from .rich_block_caption import RichBlockCaption


class InputRichBlockSlideshow(InputRichBlock):
    """
    A slideshow, corresponding to the custom HTML tag :code:`<tg-slideshow>`.

    Source: https://core.telegram.org/bots/api#inputrichblockslideshow
    """

    type: Literal[InputRichBlockType.SLIDESHOW] = InputRichBlockType.SLIDESHOW
    """Type of the block, always 'slideshow'"""
    blocks: list[InputRichBlockUnion]
    """Elements of the slideshow"""
    caption: RichBlockCaption | None = None
    """*Optional*. Caption of the block"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputRichBlockType.SLIDESHOW] = InputRichBlockType.SLIDESHOW,
            blocks: list[InputRichBlockUnion],
            caption: RichBlockCaption | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, blocks=blocks, caption=caption, **__pydantic_kwargs)
