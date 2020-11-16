from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    from .passport_file import PassportFile


class EncryptedPassportElement(TelegramObject):
    """
    Contains information about documents or other Telegram Passport elements shared with the bot
    by the user.

    Source: https://core.telegram.org/bots/api#encryptedpassportelement
    """

    type: str
    """Element type. One of 'personal_details', 'passport', 'driver_license', 'identity_card',
    'internal_passport', 'address', 'utility_bill', 'bank_statement', 'rental_agreement',
    'passport_registration', 'temporary_registration', 'phone_number', 'email'."""
    hash: str
    """Base64-encoded element hash for using in PassportElementErrorUnspecified"""
    data: Optional[str] = None
    """Base64-encoded encrypted Telegram Passport element data provided by the user, available for
    'personal_details', 'passport', 'driver_license', 'identity_card', 'internal_passport' and
    'address' types. Can be decrypted and verified using the accompanying EncryptedCredentials."""
    phone_number: Optional[str] = None
    """User's verified phone number, available only for 'phone_number' type"""
    email: Optional[str] = None
    """User's verified email address, available only for 'email' type"""
    files: Optional[List[PassportFile]] = None
    """Array of encrypted files with documents provided by the user, available for 'utility_bill',
    'bank_statement', 'rental_agreement', 'passport_registration' and 'temporary_registration'
    types. Files can be decrypted and verified using the accompanying EncryptedCredentials."""
    front_side: Optional[PassportFile] = None
    """Encrypted file with the front side of the document, provided by the user. Available for
    'passport', 'driver_license', 'identity_card' and 'internal_passport'. The file can be
    decrypted and verified using the accompanying EncryptedCredentials."""
    reverse_side: Optional[PassportFile] = None
    """Encrypted file with the reverse side of the document, provided by the user. Available for
    'driver_license' and 'identity_card'. The file can be decrypted and verified using the
    accompanying EncryptedCredentials."""
    selfie: Optional[PassportFile] = None
    """Encrypted file with the selfie of the user holding a document, provided by the user;
    available for 'passport', 'driver_license', 'identity_card' and 'internal_passport'. The
    file can be decrypted and verified using the accompanying EncryptedCredentials."""
    translation: Optional[List[PassportFile]] = None
    """Array of encrypted files with translated versions of documents provided by the user.
    Available if requested for 'passport', 'driver_license', 'identity_card',
    'internal_passport', 'utility_bill', 'bank_statement', 'rental_agreement',
    'passport_registration' and 'temporary_registration' types. Files can be decrypted and
    verified using the accompanying EncryptedCredentials."""
