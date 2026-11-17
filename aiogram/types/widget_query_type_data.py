from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from .widget_query_type import WidgetQueryType

if TYPE_CHECKING:
    from .ton_wallet_card import TonWalletCard


class WidgetQueryTypeData(WidgetQueryType):
    """
    The query contains data for the bot.

    Source: https://core.telegram.org/bots/api#widgetquerytypedata
    """

    type: Literal["data"] = "data"
    """Type of the query, always 'data'"""
    wallet_card: TonWalletCard | None = None
    """*Optional*. TON wallet card of the user who sent the query, if it was sent to the bot along with the query"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal["data"] = "data",
            wallet_card: TonWalletCard | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, wallet_card=wallet_card, **__pydantic_kwargs)
