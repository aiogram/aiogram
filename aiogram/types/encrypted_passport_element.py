import typing

from . import base
from . import fields
from .passport_file import PassportFile


class EncryptedPassportElement(base.TelegramObject):
    """
    Contains information about documents or other Telegram Passport elements shared with the bot by the user.

    https://core.telegram.org/bots/api#encryptedpassportelement
    """

    type: base.String = fields.Field()
    data: base.String = fields.Field()
    phone_number: base.String = fields.Field()
    email: base.String = fields.Field()
    files: typing.List[PassportFile] = fields.ListField(base=PassportFile)
    front_side: PassportFile = fields.Field(base=PassportFile)
    reverse_side: PassportFile = fields.Field(base=PassportFile)
    selfie: PassportFile = fields.Field(base=PassportFile)
