import typing

from . import base
from . import fields
from .photo_size import PhotoSize


class UserProfilePhotos(base.TelegramObject):
    """
    This object represent a user's profile pictures.

    https://core.telegram.org/bots/api#userprofilephotos
    """
    total_count: base.Integer = fields.Field()
    photos: typing.List[typing.List[PhotoSize]] = fields.ListOfLists(base=PhotoSize)
