from typing import TYPE_CHECKING, Any

from .base import TelegramObject


class WidgetQueryWallet(TelegramObject):
    """
    This object describes a TON wallet of the user, which is used in a query from a widget.

    Source: https://core.telegram.org/bots/api#widgetquerywallet
    """

    address: str
    """Address of the wallet"""
    amount: str
    """Balance of the wallet, in the *smallest units* of the cryptocurrency, as a decimal number"""
    public_key: str | None = None
    """*Optional*. Hex-encoded public key of the wallet; omitted if unknown"""
    state_init: str | None = None
    """*Optional*. Base64-encoded serialized StateInit of the wallet contract; omitted if and only if *public_key* is omitted"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            address: str,
            amount: str,
            public_key: str | None = None,
            state_init: str | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                address=address,
                amount=amount,
                public_key=public_key,
                state_init=state_init,
                **__pydantic_kwargs,
            )
