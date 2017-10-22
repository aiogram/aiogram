from . import base
from . import fields


class Voice(base.TelegramObject):
    """
    This object represents a voice note.

    https://core.telegram.org/bots/api#voice
    """
    file_id: base.String = fields.Field()
    duration: base.Integer = fields.Field()
    mime_type: base.String = fields.Field()
    file_size: base.Integer = fields.Field()

    def __hash__(self):
        return self.file_id

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other.file_id == self.file_id
        return self.file_id == other
