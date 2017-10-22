from . import base
from . import fields


class Audio(base.TelegramObject):
    """
    This object represents an audio file to be treated as music by the Telegram clients.

    https://core.telegram.org/bots/api#audio
    """
    file_id: base.String = fields.Field()
    duration: base.Integer = fields.Field()
    performer: base.String = fields.Field()
    title: base.String = fields.Field()
    mime_type: base.String = fields.Field()
    file_size: base.Integer = fields.Field()

    def __hash__(self):
        return self.file_id

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other.file_id == self.file_id
        return self.file_id == other
