from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from .widget_query_type import WidgetQueryType

if TYPE_CHECKING:
    from .widget_query_wallet import WidgetQueryWallet


class WidgetQueryTypeSignData(WidgetQueryType):
    """
    The query contains data signed by a TON wallet of the user who sent the query. The data is signed for the domain :code:`bot<bot_id>`, where :code:`<bot_id>` is the identifier of the bot.

    Source: https://core.telegram.org/bots/api#widgetquerytypesigndata
    """

    type: Literal["sign_data"] = "sign_data"
    """Type of the query, always 'sign_data'"""
    wallet: WidgetQueryWallet
    """The wallet that signed the data"""
    sign_data: str
    """JSON-serialized signed data"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal["sign_data"] = "sign_data",
            wallet: WidgetQueryWallet,
            sign_data: str,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, wallet=wallet, sign_data=sign_data, **__pydantic_kwargs)
