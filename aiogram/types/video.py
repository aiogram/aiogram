from . import base
from . import fields
from .photo_size import PhotoSize


class Video(base.TelegramObject):
    """
    This object represents a video file.

    https://core.telegram.org/bots/api#video
    """
    file_id: base.String = fields.Field()
    width: base.Integer = fields.Field()
    height: base.Integer = fields.Field()
    duration: base.Integer = fields.Field()
    thumb: PhotoSize = fields.Field(base=PhotoSize)
    mime_type: base.String = fields.Field()
    file_size: base.Integer = fields.Field()

    def __hash__(self):
        return self.file_id

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other.file_id == self.file_id
        return self.file_id == other
