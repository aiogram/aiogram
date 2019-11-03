from __future__ import annotations

from .base import TelegramObject


class Invoice(TelegramObject):
    """
    This object contains basic information about an invoice.

    Source: https://core.telegram.org/bots/api#invoice
    """

    title: str
    """Product name"""
    description: str
    """Product description"""
    start_parameter: str
    """Unique bot deep-linking parameter that can be used to generate this invoice"""
    currency: str
    """Three-letter ISO 4217 currency code"""
    total_amount: int
    """Total price in the smallest units of the currency (integer, not float/double). For example, for a price of US$ 1.45 pass amount = 145. See the exp parameter in currencies.json, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies)."""
