from __future__ import annotations

from typing import Optional

from .input_message_content import InputMessageContent


class InputContactMessageContent(InputMessageContent):
    """
    Represents the content of a contact message to be sent as the result of an inline query.

    Source: https://core.telegram.org/bots/api#inputcontactmessagecontent
    """

    phone_number: str
    """Contact's phone number"""
    first_name: str
    """Contact's first name"""
    last_name: Optional[str] = None
    """Contact's last name"""
    vcard: Optional[str] = None
    """Additional data about the contact in the form of a vCard, 0-2048 bytes"""
