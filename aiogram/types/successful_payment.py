from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .order_info import OrderInfo


class SuccessfulPayment(TelegramObject):
    """
    This object contains basic information about a successful payment.

    Source: https://core.telegram.org/bots/api#successfulpayment
    """

    currency: str
    """Three-letter ISO 4217 `currency <https://core.telegram.org/bots/payments#supported-currencies>`_ code"""
    total_amount: int
    """Total price in the *smallest units* of the currency (integer, **not** float/double). For example, for a price of :code:`US$ 1.45` pass :code:`amount = 145`. See the *exp* parameter in `currencies.json <https://core.telegram.org/bots/payments/currencies.json>`_, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies)."""
    invoice_payload: str
    """Bot specified invoice payload"""
    telegram_payment_charge_id: str
    """Telegram payment identifier"""
    provider_payment_charge_id: str
    """Provider payment identifier"""
    shipping_option_id: Optional[str] = None
    """*Optional*. Identifier of the shipping option chosen by the user"""
    order_info: Optional[OrderInfo] = None
    """*Optional*. Order information provided by the user"""
