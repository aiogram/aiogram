from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import InputRichBlockType
from .base import TelegramObject
from .input_rich_block import InputRichBlock

if TYPE_CHECKING:
    from .rich_block_table_cell import RichBlockTableCell
    from .rich_text_union import RichTextUnion


class InputRichBlockTable(InputRichBlock):
    """
    A table, corresponding to the HTML tag :code:`<table>`.

    Source: https://core.telegram.org/bots/api#inputrichblocktable
    """

    type: Literal[InputRichBlockType.TABLE] = InputRichBlockType.TABLE
    """Type of the block, always 'table'"""
    cells: list[list[RichBlockTableCell]]
    """Cells of the table"""
    is_bordered: bool | None = None
    """*Optional*. Pass :code:`True` if the table has borders"""
    is_striped: bool | None = None
    """*Optional*. Pass :code:`True` if the table is striped"""
    caption: RichTextUnion | None = None
    """*Optional*. Caption of the table"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputRichBlockType.TABLE] = InputRichBlockType.TABLE,
            cells: list[list[RichBlockTableCell]],
            is_bordered: bool | None = None,
            is_striped: bool | None = None,
            caption: RichTextUnion | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                cells=cells,
                is_bordered=is_bordered,
                is_striped=is_striped,
                caption=caption,
                **__pydantic_kwargs,
            )
