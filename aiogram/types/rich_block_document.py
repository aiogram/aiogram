from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import RichBlockType
from .rich_block import RichBlock

if TYPE_CHECKING:
    from .document import Document
    from .rich_block_caption import RichBlockCaption


class RichBlockDocument(RichBlock):
    """
    A block with a general file, corresponding to the custom HTML tag :code:`<tg-document>`.

    Source: https://core.telegram.org/bots/api#richblockdocument
    """

    type: Literal[RichBlockType.DOCUMENT] = RichBlockType.DOCUMENT
    """Type of the block, always 'document'"""
    document: Document
    """The document"""
    caption: RichBlockCaption | None = None
    """*Optional*. Caption of the block"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[RichBlockType.DOCUMENT] = RichBlockType.DOCUMENT,
            document: Document,
            caption: RichBlockCaption | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, document=document, caption=caption, **__pydantic_kwargs)
