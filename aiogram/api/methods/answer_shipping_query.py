from typing import Any, Dict, List, Optional

from .base import Request, TelegramMethod
from ..types import ShippingOption


class AnswerShippingQuery(TelegramMethod[bool]):
    """
    If you sent an invoice requesting a shipping address and the parameter is_flexible was specified, the Bot API will send an Update with a shipping_query field to the bot. Use this method to reply to shipping queries. On success, True is returned.

    Source: https://core.telegram.org/bots/api#answershippingquery
    """

    __returning__ = bool

    shipping_query_id: str
    """Unique identifier for the query to be answered"""

    ok: bool
    """Specify True if delivery to the specified address is possible and False if there are any problems (for example, if delivery to the specified address is not possible)"""

    shipping_options: Optional[List[ShippingOption]] = None
    """Required if ok is True. A JSON-serialized array of available shipping options."""

    error_message: Optional[str] = None
    """Required if ok is False. Error message in human readable form that explains why it is impossible to complete the order (e.g. "Sorry, delivery to your desired address is unavailable'). Telegram will display this message to the user."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})

        return Request(method="answerShippingQuery", data=data)
