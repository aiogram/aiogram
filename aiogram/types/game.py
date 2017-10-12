import typing

from . import base
from . import fields
from .animation import Animation
from .message_entity import MessageEntity
from .photo_size import PhotoSize


class Game(base.TelegramObject):
    """
    This object represents a game.

    Use BotFather to create and edit games, their short names will act as unique identifiers.

    https://core.telegram.org/bots/api#game
    """
    title: base.String = fields.Field()
    description: base.String = fields.Field()
    photo: typing.List[PhotoSize] = fields.ListField(base=PhotoSize)
    text: base.String = fields.Field()
    text_entities: typing.List[MessageEntity] = fields.ListField(base=MessageEntity)
    animation: Animation = fields.Field(base=Animation)
