from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User
    from .shipping_address import ShippingAddress


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
