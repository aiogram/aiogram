from . import base
from . import fields
from . import mixins


class Audio(base.TelegramObject, mixins.Downloadable):
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
        return hash(self.file_id) + \
               self.duration + \
               hash(self.performer) + \
               hash(self.title) + \
               hash(self.mime_type) + \
               self.file_size
