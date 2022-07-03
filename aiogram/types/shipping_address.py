from __future__ import annotations

from .base import TelegramObject


class ShippingAddress(TelegramObject):
    """
    This object represents a shipping address.

    Source: https://core.telegram.org/bots/api#shippingaddress
    """

    country_code: str
    """Two-letter ISO 3166-1 alpha-2 country code"""
    state: str
    """State, if applicable"""
    city: str
    """City"""
    street_line1: str
    """First line for the address"""
    street_line2: str
    """Second line for the address"""
    post_code: str
    """Address post code"""
