from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .location import Location


class BusinessLocation(TelegramObject):
    """


    Source: https://core.telegram.org/bots/api#businesslocation
    """

    address: str
    """Address of the business"""
    location: Optional[Location] = None
    """*Optional*. Location of the business"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            address: str,
            location: Optional[Location] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(address=address, location=location, **__pydantic_kwargs)
