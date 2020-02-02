from typing import Any, Dict, List, Optional

from ..types import InlineKeyboardMarkup, LabeledPrice, Message
from .base import Request, TelegramMethod


class SendInvoice(TelegramMethod[Message]):
    """
    Use this method to send invoices. On success, the sent Message is returned.

    Source: https://core.telegram.org/bots/api#sendinvoice
    """

    __returning__ = Message

    chat_id: int
    """Unique identifier for the target private chat"""
    title: str
    """Product name, 1-32 characters"""
    description: str
    """Product description, 1-255 characters"""
    payload: str
    """Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for
    your internal processes."""
    provider_token: str
    """Payments provider token, obtained via Botfather"""
    start_parameter: str
    """Unique deep-linking parameter that can be used to generate this invoice when used as a
    start parameter"""
    currency: str
    """Three-letter ISO 4217 currency code, see more on currencies"""
    prices: List[LabeledPrice]
    """Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount,
    delivery cost, delivery tax, bonus, etc.)"""
    provider_data: Optional[str] = None
    """JSON-encoded data about the invoice, which will be shared with the payment provider. A
    detailed description of required fields should be provided by the payment provider."""
    photo_url: Optional[str] = None
    """URL of the product photo for the invoice. Can be a photo of the goods or a marketing image
    for a service. People like it better when they see what they are paying for."""
    photo_size: Optional[int] = None
    """Photo size"""
    photo_width: Optional[int] = None
    """Photo width"""
    photo_height: Optional[int] = None
    """Photo height"""
    need_name: Optional[bool] = None
    """Pass True, if you require the user's full name to complete the order"""
    need_phone_number: Optional[bool] = None
    """Pass True, if you require the user's phone number to complete the order"""
    need_email: Optional[bool] = None
    """Pass True, if you require the user's email address to complete the order"""
    need_shipping_address: Optional[bool] = None
    """Pass True, if you require the user's shipping address to complete the order"""
    send_phone_number_to_provider: Optional[bool] = None
    """Pass True, if user's phone number should be sent to provider"""
    send_email_to_provider: Optional[bool] = None
    """Pass True, if user's email address should be sent to provider"""
    is_flexible: Optional[bool] = None
    """Pass True, if the final price depends on the shipping method"""
    disable_notification: Optional[bool] = None
    """Sends the message silently. Users will receive a notification with no sound."""
    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for an inline keyboard. If empty, one 'Pay total price' button
    will be shown. If not empty, the first button must be a Pay button."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="sendInvoice", data=data)
