from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .passport_file import PassportFile


class EncryptedPassportElement(TelegramObject):
    """
    Describes documents or other Telegram Passport elements shared with the bot by the user.

    Source: https://core.telegram.org/bots/api#encryptedpassportelement
    """

    type: str
    """Element type. One of 'personal_details', 'passport', 'driver_license', 'identity_card', 'internal_passport', 'address', 'utility_bill', 'bank_statement', 'rental_agreement', 'passport_registration', 'temporary_registration', 'phone_number', 'email'."""
    hash: str
    """Base64-encoded element hash for using in :class:`aiogram.types.passport_element_error_unspecified.PassportElementErrorUnspecified`"""
    data: Optional[str] = None
    """*Optional*. Base64-encoded encrypted Telegram Passport element data provided by the user, available for 'personal_details', 'passport', 'driver_license', 'identity_card', 'internal_passport' and 'address' types. Can be decrypted and verified using the accompanying :class:`aiogram.types.encrypted_credentials.EncryptedCredentials`."""
    phone_number: Optional[str] = None
    """*Optional*. User's verified phone number, available only for 'phone_number' type"""
    email: Optional[str] = None
    """*Optional*. User's verified email address, available only for 'email' type"""
    files: Optional[List[PassportFile]] = None
    """*Optional*. Array of encrypted files with documents provided by the user, available for 'utility_bill', 'bank_statement', 'rental_agreement', 'passport_registration' and 'temporary_registration' types. Files can be decrypted and verified using the accompanying :class:`aiogram.types.encrypted_credentials.EncryptedCredentials`."""
    front_side: Optional[PassportFile] = None
    """*Optional*. Encrypted file with the front side of the document, provided by the user. Available for 'passport', 'driver_license', 'identity_card' and 'internal_passport'. The file can be decrypted and verified using the accompanying :class:`aiogram.types.encrypted_credentials.EncryptedCredentials`."""
    reverse_side: Optional[PassportFile] = None
    """*Optional*. Encrypted file with the reverse side of the document, provided by the user. Available for 'driver_license' and 'identity_card'. The file can be decrypted and verified using the accompanying :class:`aiogram.types.encrypted_credentials.EncryptedCredentials`."""
    selfie: Optional[PassportFile] = None
    """*Optional*. Encrypted file with the selfie of the user holding a document, provided by the user; available for 'passport', 'driver_license', 'identity_card' and 'internal_passport'. The file can be decrypted and verified using the accompanying :class:`aiogram.types.encrypted_credentials.EncryptedCredentials`."""
    translation: Optional[List[PassportFile]] = None
    """*Optional*. Array of encrypted files with translated versions of documents provided by the user. Available if requested for 'passport', 'driver_license', 'identity_card', 'internal_passport', 'utility_bill', 'bank_statement', 'rental_agreement', 'passport_registration' and 'temporary_registration' types. Files can be decrypted and verified using the accompanying :class:`aiogram.types.encrypted_credentials.EncryptedCredentials`."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: str,
            hash: str,
            data: Optional[str] = None,
            phone_number: Optional[str] = None,
            email: Optional[str] = None,
            files: Optional[List[PassportFile]] = None,
            front_side: Optional[PassportFile] = None,
            reverse_side: Optional[PassportFile] = None,
            selfie: Optional[PassportFile] = None,
            translation: Optional[List[PassportFile]] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                hash=hash,
                data=data,
                phone_number=phone_number,
                email=email,
                files=files,
                front_side=front_side,
                reverse_side=reverse_side,
                selfie=selfie,
                translation=translation,
                **__pydantic_kwargs,
            )
