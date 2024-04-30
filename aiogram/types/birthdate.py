from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject


class Birthdate(TelegramObject):
    """


    Source: https://core.telegram.org/bots/api#birthdate
    """

    day: int
    """Day of the user's birth; 1-31"""
    month: int
    """Month of the user's birth; 1-12"""
    year: Optional[int] = None
    """*Optional*. Year of the user's birth"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            day: int,
            month: int,
            year: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(day=day, month=month, year=year, **__pydantic_kwargs)
