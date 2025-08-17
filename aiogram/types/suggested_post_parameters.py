from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .suggested_post_price import SuggestedPostPrice


class SuggestedPostParameters(TelegramObject):
    """
    Contains parameters of a post that is being suggested by the bot.

    Source: https://core.telegram.org/bots/api#suggestedpostparameters
    """

    price: Optional[SuggestedPostPrice] = None
    """*Optional*. Proposed price for the post. If the field is omitted, then the post is unpaid."""
    send_date: Optional[int] = None
    """*Optional*. Proposed send date of the post. If specified, then the date must be between 300 second and 2678400 seconds (30 days) in the future. If the field is omitted, then the post can be published at any time within 30 days at the sole discretion of the user who approves it."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            price: Optional[SuggestedPostPrice] = None,
            send_date: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(price=price, send_date=send_date, **__pydantic_kwargs)
