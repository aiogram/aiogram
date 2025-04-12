from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject


class LocationAddress(TelegramObject):
    """
    Describes the physical address of a location.

    Source: https://core.telegram.org/bots/api#locationaddress
    """

    country_code: str
    """The two-letter ISO 3166-1 alpha-2 country code of the country where the location is located"""
    state: Optional[str] = None
    """*Optional*. State of the location"""
    city: Optional[str] = None
    """*Optional*. City of the location"""
    street: Optional[str] = None
    """*Optional*. Street address of the location"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            country_code: str,
            state: Optional[str] = None,
            city: Optional[str] = None,
            street: Optional[str] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                country_code=country_code,
                state=state,
                city=city,
                street=street,
                **__pydantic_kwargs,
            )
