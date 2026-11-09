from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from .widget_query_type import WidgetQueryType

if TYPE_CHECKING:
    from .widget_query_wallet import WidgetQueryWallet


class WidgetQueryTypeSentTransaction(WidgetQueryType):
    """
    The query notifies the bot about a transaction sent from a TON wallet of the user who sent the query.

    Source: https://core.telegram.org/bots/api#widgetquerytypesenttransaction
    """

    type: Literal["sent_transaction"] = "sent_transaction"
    """Type of the query, always 'sent_transaction'"""
    wallet: WidgetQueryWallet
    """The wallet from which the transaction was sent"""
    msg_hash: str
    """Value of *msg_hash* of the transaction"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal["sent_transaction"] = "sent_transaction",
            wallet: WidgetQueryWallet,
            msg_hash: str,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, wallet=wallet, msg_hash=msg_hash, **__pydantic_kwargs)
