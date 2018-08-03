from . import base
from . import fields
import typing
from .encrypted_passport_element import EncryptedPassportElement
from .encrypted_credentials import EncryptedCredentials


class PassportData(base.TelegramObject):
    """
    Contains information about Telegram Passport data shared with the bot by the user.

    https://core.telegram.org/bots/api#passportdata
    """

    data: typing.List[EncryptedPassportElement] = fields.ListField(base=EncryptedPassportElement)
    credentials: EncryptedCredentials = fields.Field(base=EncryptedCredentials)
