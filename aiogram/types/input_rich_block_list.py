from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import InputRichBlockType
from .base import TelegramObject
from .input_rich_block import InputRichBlock

if TYPE_CHECKING:
    from .input_rich_block_list_item import InputRichBlockListItem


class InputRichBlockList(InputRichBlock):
    """
    A list of blocks, corresponding to the HTML tag :code:`<ul>` or :code:`<ol>` with multiple nested tags :code:`<li>`.

    Source: https://core.telegram.org/bots/api#inputrichblocklist
    """

    type: Literal[InputRichBlockType.LIST] = InputRichBlockType.LIST
    """Type of the block, always 'list'"""
    items: list[InputRichBlockListItem]
    """Items of the list"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputRichBlockType.LIST] = InputRichBlockType.LIST,
            items: list[InputRichBlockListItem],
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, items=items, **__pydantic_kwargs)
