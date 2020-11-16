from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    from .shipping_address import ShippingAddress


class OrderInfo(TelegramObject):
    """
    This object represents information about an order.

    Source: https://core.telegram.org/bots/api#orderinfo
    """

    name: Optional[str] = None
    """User name"""
    phone_number: Optional[str] = None
    """User's phone number"""
    email: Optional[str] = None
    """User email"""
    shipping_address: Optional[ShippingAddress] = None
    """User shipping address"""
