from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .sticker import Sticker


class Gift(TelegramObject):
    """
    This object represents a gift that can be sent by the bot.

    Source: https://core.telegram.org/bots/api#gift
    """

    id: str
    """Unique identifier of the gift"""
    sticker: Sticker
    """The sticker that represents the gift"""
    star_count: int
    """The number of Telegram Stars that must be paid to send the sticker"""
    total_count: Optional[int] = None
    """*Optional*. The total number of the gifts of this type that can be sent; for limited gifts only"""
    remaining_count: Optional[int] = None
    """*Optional*. The number of remaining gifts of this type that can be sent; for limited gifts only"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: str,
            sticker: Sticker,
            star_count: int,
            total_count: Optional[int] = None,
            remaining_count: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                id=id,
                sticker=sticker,
                star_count=star_count,
                total_count=total_count,
                remaining_count=remaining_count,
                **__pydantic_kwargs,
            )
