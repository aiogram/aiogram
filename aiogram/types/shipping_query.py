from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from ..methods import AnswerShippingQuery
    from ..types import ShippingOption
    from .shipping_address import ShippingAddress
    from .user import User


class ShippingQuery(TelegramObject):
    """
    This object contains information about an incoming shipping query.

    Source: https://core.telegram.org/bots/api#shippingquery
    """

    id: str
    """Unique query identifier"""
    from_user: User = Field(..., alias="from")
    """User who sent the query"""
    invoice_payload: str
    """Bot specified invoice payload"""
    shipping_address: ShippingAddress
    """User specified shipping address"""

    def answer(
        self,
        ok: bool,
        shipping_options: Optional[List[ShippingOption]] = None,
        error_message: Optional[str] = None,
    ) -> AnswerShippingQuery:
        """
        :param ok:
        :param shipping_options:
        :param error_message:
        :return:
        """
        from ..methods import AnswerShippingQuery

        return AnswerShippingQuery(
            shipping_query_id=self.id,
            ok=ok,
            shipping_options=shipping_options,
            error_message=error_message,
        )
