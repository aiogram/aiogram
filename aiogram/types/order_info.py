from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .shipping_address import ShippingAddress


class OrderInfo(TelegramObject):
    """
    This object represents information about an order.

    Source: https://core.telegram.org/bots/api#orderinfo
    """

    name: Optional[str] = None
    """*Optional*. User name"""
    phone_number: Optional[str] = None
    """*Optional*. User's phone number"""
    email: Optional[str] = None
    """*Optional*. User email"""
    shipping_address: Optional[ShippingAddress] = None
    """*Optional*. User shipping address"""
