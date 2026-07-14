from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import InputRichBlockType
from .base import TelegramObject
from .input_rich_block import InputRichBlock

if TYPE_CHECKING:
    from .input_rich_block import InputRichBlock
    from .input_rich_block_union import InputRichBlockUnion
    from .rich_text_union import RichTextUnion


class InputRichBlockBlockQuotation(InputRichBlock):
    """
    A block quotation, corresponding to the HTML tag :code:`<blockquote>`.

    Source: https://core.telegram.org/bots/api#inputrichblockblockquotation
    """

    type: Literal[InputRichBlockType.BLOCKQUOTE] = InputRichBlockType.BLOCKQUOTE
    """Type of the block, always 'blockquote'"""
    blocks: list[InputRichBlockUnion]
    """Content of the block"""
    credit: RichTextUnion | None = None
    """*Optional*. Credit of the block"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputRichBlockType.BLOCKQUOTE] = InputRichBlockType.BLOCKQUOTE,
            blocks: list[InputRichBlockUnion],
            credit: RichTextUnion | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, blocks=blocks, credit=credit, **__pydantic_kwargs)
