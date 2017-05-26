from aiogram.types.animation import Animation
from aiogram.types.message_entity import MessageEntity
from aiogram.types.photo_size import PhotoSize
from . import Deserializable


class Game(Deserializable):
    def __init__(self, title, description, photo, text, text_entities, animation):
        self.title = title
        self.description = description
        self.photo = photo
        self.text = text
        self.text_entities = text_entities
        self.animation = animation

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        title = raw_data.get('title')
        description = raw_data.get('description')
        photo = PhotoSize.deserialize_array(raw_data.get('photo'))
        text = raw_data.get('text')
        text_entities = MessageEntity.deserialize_array(raw_data.get('text_entities'))
        animation = Animation.deserialize(raw_data.get('animation'))

        return Game(title, description, photo, text, text_entities, animation)
