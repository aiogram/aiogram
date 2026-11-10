from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import RichTextType
from .rich_text import RichText

if TYPE_CHECKING:
    from .rich_text_union import RichTextUnion


class RichTextTonAddress(RichText):
    """
    An address in the TON blockchain.

    Source: https://core.telegram.org/bots/api#richtexttonaddress
    """

    type: Literal[RichTextType.TON_ADDRESS] = RichTextType.TON_ADDRESS
    """Type of the rich text, always 'ton_address'"""
    text: RichTextUnion
    """Text of the address"""
    address: str
    """The address"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[RichTextType.TON_ADDRESS] = RichTextType.TON_ADDRESS,
            text: RichTextUnion,
            address: str,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, text=text, address=address, **__pydantic_kwargs)
