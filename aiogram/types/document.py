from . import base
from . import fields
from .photo_size import PhotoSize


class Document(base.TelegramObject):
    """
    This object represents a general file (as opposed to photos, voice messages and audio files).

    https://core.telegram.org/bots/api#document
    """
    file_id: base.String = fields.Field()
    thumb: PhotoSize = fields.Field(base=PhotoSize)
    file_name: base.String = fields.Field()
    mime_type: base.String = fields.Field()
    file_size: base.Integer = fields.Field()

    def __hash__(self):
        return self.file_id

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other.file_id == self.file_id
        return self.file_id == other
