from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional, Union

from ..enums import InlineQueryResultType
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_contact_message_content import InputContactMessageContent
    from .input_invoice_message_content import InputInvoiceMessageContent
    from .input_location_message_content import InputLocationMessageContent
    from .input_text_message_content import InputTextMessageContent
    from .input_venue_message_content import InputVenueMessageContent


class InlineQueryResultContact(InlineQueryResult):
    """
    Represents a contact with a phone number. By default, this contact will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the contact.
    **Note:** This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultcontact
    """

    type: Literal[InlineQueryResultType.CONTACT] = InlineQueryResultType.CONTACT
    """Type of the result, must be *contact*"""
    id: str
    """Unique identifier for this result, 1-64 Bytes"""
    phone_number: str
    """Contact's phone number"""
    first_name: str
    """Contact's first name"""
    last_name: Optional[str] = None
    """*Optional*. Contact's last name"""
    vcard: Optional[str] = None
    """*Optional*. Additional data about the contact in the form of a `vCard <https://en.wikipedia.org/wiki/VCard>`_, 0-2048 bytes"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_ attached to the message"""
    input_message_content: Optional[
        Union[
            InputTextMessageContent,
            InputLocationMessageContent,
            InputVenueMessageContent,
            InputContactMessageContent,
            InputInvoiceMessageContent,
        ]
    ] = None
    """*Optional*. Content of the message to be sent instead of the contact"""
    thumbnail_url: Optional[str] = None
    """*Optional*. Url of the thumbnail for the result"""
    thumbnail_width: Optional[int] = None
    """*Optional*. Thumbnail width"""
    thumbnail_height: Optional[int] = None
    """*Optional*. Thumbnail height"""
