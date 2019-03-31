import typing

from . import base
from . import fields
from .encrypted_credentials import EncryptedCredentials
from .encrypted_passport_element import EncryptedPassportElement


class PassportData(base.TelegramObject):
    """
    Contains information about Telegram Passport data shared with the bot by the user.

    https://core.telegram.org/bots/api#passportdata
    """

    data: typing.List[EncryptedPassportElement] = fields.ListField(base=EncryptedPassportElement)
    credentials: EncryptedCredentials = fields.Field(base=EncryptedCredentials)
