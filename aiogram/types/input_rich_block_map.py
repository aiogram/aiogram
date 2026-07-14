from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..enums import InputRichBlockType
from .base import TelegramObject
from .input_rich_block import InputRichBlock

if TYPE_CHECKING:
    from .location import Location
    from .rich_block_caption import RichBlockCaption


class InputRichBlockMap(InputRichBlock):
    """
    A block with a map, corresponding to the custom HTML tag :code:`<tg-map>`. The map's width and height must not exceed 10000 in total. The width and height ratio must be at most 20.

    Source: https://core.telegram.org/bots/api#inputrichblockmap
    """

    type: Literal[InputRichBlockType.MAP] = InputRichBlockType.MAP
    """Type of the block, always 'map'"""
    location: Location
    """Location of the center of the map"""
    zoom: int
    """Map zoom level; 0-24"""
    width: int
    """Map width; 0-10000"""
    height: int
    """Map height; 0-10000"""
    caption: RichBlockCaption | None = None
    """*Optional*. Caption of the block"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InputRichBlockType.MAP] = InputRichBlockType.MAP,
            location: Location,
            zoom: int,
            width: int,
            height: int,
            caption: RichBlockCaption | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                location=location,
                zoom=zoom,
                width=width,
                height=height,
                caption=caption,
                **__pydantic_kwargs,
            )
