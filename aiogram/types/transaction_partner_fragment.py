from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from ..enums import TransactionPartnerType
from .transaction_partner import TransactionPartner

if TYPE_CHECKING:
    from .revenue_withdrawal_state_failed import RevenueWithdrawalStateFailed
    from .revenue_withdrawal_state_pending import RevenueWithdrawalStatePending
    from .revenue_withdrawal_state_succeeded import RevenueWithdrawalStateSucceeded


class TransactionPartnerFragment(TransactionPartner):
    """
    Describes a withdrawal transaction with Fragment.

    Source: https://core.telegram.org/bots/api#transactionpartnerfragment
    """

    type: Literal[TransactionPartnerType.FRAGMENT] = TransactionPartnerType.FRAGMENT
    """Type of the transaction partner, always 'fragment'"""
    withdrawal_state: Optional[
        Union[
            RevenueWithdrawalStatePending,
            RevenueWithdrawalStateSucceeded,
            RevenueWithdrawalStateFailed,
        ]
    ] = None
    """*Optional*. State of the transaction if the transaction is outgoing"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[TransactionPartnerType.FRAGMENT] = TransactionPartnerType.FRAGMENT,
            withdrawal_state: Optional[
                Union[
                    RevenueWithdrawalStatePending,
                    RevenueWithdrawalStateSucceeded,
                    RevenueWithdrawalStateFailed,
                ]
            ] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, withdrawal_state=withdrawal_state, **__pydantic_kwargs)
