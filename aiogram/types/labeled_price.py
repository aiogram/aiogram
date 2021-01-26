from __future__ import annotations

from .base import MutableTelegramObject


class LabeledPrice(MutableTelegramObject):
    """
    This object represents a portion of the price for goods or services.

    Source: https://core.telegram.org/bots/api#labeledprice
    """

    label: str
    """Portion label"""
    amount: int
    """Price of the product in the *smallest units* of the `currency <https://core.telegram.org/bots/payments#supported-currencies>`_ (integer, **not** float/double). For example, for a price of :code:`US$ 1.45` pass :code:`amount = 145`. See the *exp* parameter in `currencies.json <https://core.telegram.org/bots/payments/currencies.json>`_, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies)."""
