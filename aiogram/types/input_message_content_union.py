from __future__ import annotations

from typing import TypeAlias

from .input_contact_message_content import InputContactMessageContent
from .input_invoice_message_content import InputInvoiceMessageContent
from .input_location_message_content import InputLocationMessageContent
from .input_rich_message_content import InputRichMessageContent
from .input_shared_widget_message_content import InputSharedWidgetMessageContent
from .input_text_message_content import InputTextMessageContent
from .input_venue_message_content import InputVenueMessageContent
from .input_widget_message_content import InputWidgetMessageContent

InputMessageContentUnion: TypeAlias = (
    InputTextMessageContent
    | InputRichMessageContent
    | InputLocationMessageContent
    | InputVenueMessageContent
    | InputContactMessageContent
    | InputInvoiceMessageContent
    | InputWidgetMessageContent
    | InputSharedWidgetMessageContent
)
