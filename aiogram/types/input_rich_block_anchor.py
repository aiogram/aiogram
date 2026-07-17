from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import InputRichBlockType
from .base import TelegramObject
from .input_rich_block import InputRichBlock


class InputRichBlockAnchor(InputRichBlock):
    """
    A block with an anchor, corresponding to the HTML tag :code:`<a>` with the attribute :code:`name`.

    Source: https://core.telegram.org/bots/api#inputrichblockanchor
    """

    type: Literal[InputRichBlockType.ANCHOR] = InputRichBlockType.ANCHOR
    """Type of the block, always 'anchor'"""
    name: str
    """The name of the anchor"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputRichBlockType.ANCHOR] = InputRichBlockType.ANCHOR,
            name: str,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, name=name, **__pydantic_kwargs)
