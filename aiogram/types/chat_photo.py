from . import base
from . import fields


class ChatPhoto(base.TelegramObject):
    """
    This object represents a chat photo.

    https://core.telegram.org/bots/api#chatphoto
    """
    small_file_id: base.String = fields.Field()
    big_file_id: base.String = fields.Field()
