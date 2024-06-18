from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from .base import TelegramObject
from .custom import DateTime

if TYPE_CHECKING:
    from .transaction_partner_fragment import TransactionPartnerFragment
    from .transaction_partner_other import TransactionPartnerOther
    from .transaction_partner_user import TransactionPartnerUser


class StarTransaction(TelegramObject):
    """
    Describes a Telegram Star transaction.

    Source: https://core.telegram.org/bots/api#startransaction
    """

    id: str
    """Unique identifier of the transaction. Coincides with the identifer of the original transaction for refund transactions. Coincides with *SuccessfulPayment.telegram_payment_charge_id* for successful incoming payments from users."""
    amount: int
    """Number of Telegram Stars transferred by the transaction"""
    date: DateTime
    """Date the transaction was created in Unix time"""
    source: Optional[
        Union[TransactionPartnerFragment, TransactionPartnerUser, TransactionPartnerOther]
    ] = None
    """*Optional*. Source of an incoming transaction (e.g., a user purchasing goods or services, Fragment refunding a failed withdrawal). Only for incoming transactions"""
    receiver: Optional[
        Union[TransactionPartnerFragment, TransactionPartnerUser, TransactionPartnerOther]
    ] = None
    """*Optional*. Receiver of an outgoing transaction (e.g., a user for a purchase refund, Fragment for a withdrawal). Only for outgoing transactions"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: str,
            amount: int,
            date: DateTime,
            source: Optional[
                Union[TransactionPartnerFragment, TransactionPartnerUser, TransactionPartnerOther]
            ] = None,
            receiver: Optional[
                Union[TransactionPartnerFragment, TransactionPartnerUser, TransactionPartnerOther]
            ] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                id=id,
                amount=amount,
                date=date,
                source=source,
                receiver=receiver,
                **__pydantic_kwargs,
            )
