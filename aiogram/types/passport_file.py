from . import base
from . import fields


class PassportFile(base.TelegramObject):
    """
    This object represents a file uploaded to Telegram Passport.
    Currently all Telegram Passport files are in JPEG format when decrypted and don't exceed 10MB.

    https://core.telegram.org/bots/api#passportfile
    """
    file_id: base.String = fields.Field()
    file_unique_id: base.String = fields.Field()
    file_size: base.Integer = fields.Field()
    file_date: base.Integer = fields.Field()
