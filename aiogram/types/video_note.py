from . import base
from . import fields
from .photo_size import PhotoSize


class VideoNote(base.TelegramObject):
    """
    This object represents a video message (available in Telegram apps as of v.4.0).

    https://core.telegram.org/bots/api#videonote
    """
    file_id: base.String = fields.Field()
    length: base.Integer = fields.Field()
    duration: base.Integer = fields.Field()
    thumb: PhotoSize = fields.Field(base=PhotoSize)
    file_size: base.Integer = fields.Field()

    def __hash__(self):
        return self.file_id

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other.file_id == self.file_id
        return self.file_id == other
