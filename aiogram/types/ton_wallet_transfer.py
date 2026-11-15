from typing import TYPE_CHECKING, Any

from .base import TelegramObject


class TonWalletTransfer(TelegramObject):
    """
    Describes a service message about a transfer with a TON wallet.

    Source: https://core.telegram.org/bots/api#tonwallettransfer
    """

    transaction_id: str
    """Unique identifier of the transaction; may be empty if the transfer hasn't been sent yet"""
    peer_address: str
    """Address of the transfer peer in the TON blockchain"""
    amount: str
    """The amount of transferred cryptocurrency, in the *smallest units* of the cryptocurrency, as a decimal number; negative for outgoing transfers"""
    comment: str | None = None
    """*Optional*. Comment added to the transfer; omitted if the comment is encrypted"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            transaction_id: str,
            peer_address: str,
            amount: str,
            comment: str | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                transaction_id=transaction_id,
                peer_address=peer_address,
                amount=amount,
                comment=comment,
                **__pydantic_kwargs,
            )
