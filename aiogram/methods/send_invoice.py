from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..types import InlineKeyboardMarkup, LabeledPrice, Message
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class SendInvoice(TelegramMethod[Message]):
    """
    Use this method to send invoices. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#sendinvoice
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    title: str
    """Product name, 1-32 characters"""
    description: str
    """Product description, 1-255 characters"""
    payload: str
    """Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes."""
    provider_token: str
    """Payment provider token, obtained via `@BotFather <https://t.me/botfather>`_"""
    currency: str
    """Three-letter ISO 4217 currency code, see `more on currencies <https://core.telegram.org/bots/payments#supported-currencies>`_"""
    prices: List[LabeledPrice]
    """Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)"""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    max_tip_amount: Optional[int] = None
    """The maximum accepted amount for tips in the *smallest units* of the currency (integer, **not** float/double). For example, for a maximum tip of :code:`US$ 1.45` pass :code:`max_tip_amount = 145`. See the *exp* parameter in `currencies.json <https://core.telegram.org/bots/payments/currencies.json>`_, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0"""
    suggested_tip_amounts: Optional[List[int]] = None
    """A JSON-serialized array of suggested amounts of tips in the *smallest units* of the currency (integer, **not** float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed *max_tip_amount*."""
    start_parameter: Optional[str] = None
    """Unique deep-linking parameter. If left empty, **forwarded copies** of the sent message will have a *Pay* button, allowing multiple users to pay directly from the forwarded message, using the same invoice. If non-empty, forwarded copies of the sent message will have a *URL* button with a deep link to the bot (instead of a *Pay* button), with the value used as the start parameter"""
    provider_data: Optional[str] = None
    """JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider."""
    photo_url: Optional[str] = None
    """URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for."""
    photo_size: Optional[int] = None
    """Photo size in bytes"""
    photo_width: Optional[int] = None
    """Photo width"""
    photo_height: Optional[int] = None
    """Photo height"""
    need_name: Optional[bool] = None
    """Pass :code:`True` if you require the user's full name to complete the order"""
    need_phone_number: Optional[bool] = None
    """Pass :code:`True` if you require the user's phone number to complete the order"""
    need_email: Optional[bool] = None
    """Pass :code:`True` if you require the user's email address to complete the order"""
    need_shipping_address: Optional[bool] = None
    """Pass :code:`True` if you require the user's shipping address to complete the order"""
    send_phone_number_to_provider: Optional[bool] = None
    """Pass :code:`True` if the user's phone number should be sent to provider"""
    send_email_to_provider: Optional[bool] = None
    """Pass :code:`True` if the user's email address should be sent to provider"""
    is_flexible: Optional[bool] = None
    """Pass :code:`True` if the final price depends on the shipping method"""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[bool] = None
    """Protects the contents of the sent message from forwarding and saving"""
    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""
    allow_sending_without_reply: Optional[bool] = None
    """Pass :code:`True` if the message should be sent even if the specified replied-to message is not found"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_. If empty, one 'Pay :code:`total price`' button will be shown. If not empty, the first button must be a Pay button."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="sendInvoice", data=data)
