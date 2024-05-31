from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .order_info import OrderInfo


class SuccessfulPayment(TelegramObject):
    """
    This object contains basic information about a successful payment.

    Source: https://core.telegram.org/bots/api#successfulpayment
    """

    currency: str
    """Three-letter ISO 4217 `currency <https://core.telegram.org/bots/payments#supported-currencies>`_ code, or 'XTR' for payments in `Telegram Stars <https://t.me/BotNews/90>`_"""
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

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            currency: str,
            total_amount: int,
            invoice_payload: str,
            telegram_payment_charge_id: str,
            provider_payment_charge_id: str,
            shipping_option_id: Optional[str] = None,
            order_info: Optional[OrderInfo] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                currency=currency,
                total_amount=total_amount,
                invoice_payload=invoice_payload,
                telegram_payment_charge_id=telegram_payment_charge_id,
                provider_payment_charge_id=provider_payment_charge_id,
                shipping_option_id=shipping_option_id,
                order_info=order_info,
                **__pydantic_kwargs,
            )
