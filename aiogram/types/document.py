from . import base
from . import fields
from . import mixins
from .photo_size import PhotoSize
from ..utils import helper


class Document(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a general file (as opposed to photos, voice messages and audio files).

    https://core.telegram.org/bots/api#document
    """
    file_id: base.String = fields.Field()
    file_unique_id: base.String = fields.Field()
    thumb: PhotoSize = fields.Field(base=PhotoSize)
    file_name: base.String = fields.Field()
    mime_type: base.String = fields.Field()
    file_size: base.Integer = fields.Field()

    @property
    def mime_base(self) -> str:
        base_type, _, _ = self.mime_type.partition('/')
        return base_type

    @property
    def mime_subtype(self) -> str:
        _, _, subtype = self.mime_type.partition('/')
        return subtype


class MimeBase(helper.Helper):
    """
    List of mime base types registered in IANA

    https://www.iana.org/assignments/media-types/media-types.xhtml
    """

    mode = helper.HelperMode.lowercase

    APPLICATION = helper.Item()  # application
    AUDIO = helper.Item()  # audio
    EXAMPLE = helper.Item()  # example
    FONT = helper.Item()  # font
    IMAGE = helper.Item()  # image
    MESSAGE = helper.Item()  # message
    MODEL = helper.Item()  # model
    MULTIPART = helper.Item()  # multipart
    TEXT = helper.Item()  # text
    VIDEO = helper.Item()  # video
