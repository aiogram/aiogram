from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from .base import TelegramObject
from .rich_text import RichText

if TYPE_CHECKING:
    from .rich_text import RichText
    from .rich_text_union import RichTextUnion


class RichTextCashtag(RichText):
    """
    A cashtag.

    Source: https://core.telegram.org/bots/api#richtextcashtag
    """

    type: Literal["cashtag"] = "cashtag"
    """Type of the rich text, always 'cashtag'"""
    text: RichTextUnion
    """The text"""
    cashtag: str
    """The cashtag"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal["cashtag"] = "cashtag",
            text: RichTextUnion,
            cashtag: str,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, text=text, cashtag=cashtag, **__pydantic_kwargs)
