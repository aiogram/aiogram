from . import base
from . import fields


class EncryptedCredentials(base.TelegramObject):
    """
    Contains data required for decrypting and authenticating EncryptedPassportElement.
    See the Telegram Passport Documentation for a complete description of the data decryption
    and authentication processes.

    https://core.telegram.org/bots/api#encryptedcredentials
    """

    data: base.String = fields.Field()
    hash: base.String = fields.Field()
    secret: base.String = fields.Field()
