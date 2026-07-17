from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import InputRichBlockType
from .base import TelegramObject
from .input_rich_block import InputRichBlock

if TYPE_CHECKING:
    from .input_rich_block import InputRichBlock
    from .input_rich_block_union import InputRichBlockUnion
    from .rich_block_caption import RichBlockCaption


class InputRichBlockCollage(InputRichBlock):
    """
    A collage, corresponding to the custom HTML tag :code:`<tg-collage>`.

    Source: https://core.telegram.org/bots/api#inputrichblockcollage
    """

    type: Literal[InputRichBlockType.COLLAGE] = InputRichBlockType.COLLAGE
    """Type of the block, always 'collage'"""
    blocks: list[InputRichBlockUnion]
    """Elements of the collage"""
    caption: RichBlockCaption | None = None
    """*Optional*. Caption of the block"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputRichBlockType.COLLAGE] = InputRichBlockType.COLLAGE,
            blocks: list[InputRichBlockUnion],
            caption: RichBlockCaption | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, blocks=blocks, caption=caption, **__pydantic_kwargs)
