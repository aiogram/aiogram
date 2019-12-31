from . import base
from . import fields
from . import mixins


class File(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a file ready to be downloaded.

    The file can be downloaded via the link https://api.telegram.org/file/bot<token>/<file_path>.

    It is guaranteed that the link will be valid for at least 1 hour.
    When the link expires, a new one can be requested by calling getFile.

    Maximum file size to download is 20 MB

    https://core.telegram.org/bots/api#file
    """
    file_id: base.String = fields.Field()
    file_unique_id: base.String = fields.Field()
    file_size: base.Integer = fields.Field()
    file_path: base.String = fields.Field()
