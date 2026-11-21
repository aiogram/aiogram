from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User


class BotSubscriptionUpdated(TelegramObject):
    """
    This object contains information about changes to a user payment subscription toward the current bot.

    Source: https://core.telegram.org/bots/api#botsubscriptionupdated
    """

    user: User
    """User who subscribed for payments toward the bot"""
    invoice_payload: str
    """Bot-specified invoice payload"""
    state: str
    """The new state of the subscription. Currently, it can be one of 'canceled' if the user canceled the subscription, 'active' if the user re-enabled a previously canceled subscription, or 'failed' if payment for the subscription failed"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            user: User,
            invoice_payload: str,
            state: str,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                user=user, invoice_payload=invoice_payload, state=state, **__pydantic_kwargs
            )
