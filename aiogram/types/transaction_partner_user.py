from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional

from ..enums import TransactionPartnerType
from .transaction_partner import TransactionPartner

if TYPE_CHECKING:
    from .user import User


class TransactionPartnerUser(TransactionPartner):
    """
    Describes a transaction with a user.

    Source: https://core.telegram.org/bots/api#transactionpartneruser
    """

    type: Literal[TransactionPartnerType.USER] = TransactionPartnerType.USER
    """Type of the transaction partner, always 'user'"""
    user: User
    """Information about the user"""
    invoice_payload: Optional[str] = None
    """*Optional*. Bot-specified invoice payload"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[TransactionPartnerType.USER] = TransactionPartnerType.USER,
            user: User,
            invoice_payload: Optional[str] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type, user=user, invoice_payload=invoice_payload, **__pydantic_kwargs
            )
