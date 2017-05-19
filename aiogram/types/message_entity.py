from aiogram.types import Deserializable
from aiogram.types.user import User


class MessageEntity(Deserializable):
    __slots__ = ('data', 'type', 'offset', 'length', 'url', 'user')

    def __init__(self, data, type, offset, length, url, user):
        self.data = data

        self.type = type
        self.offset = offset
        self.length = length
        self.url = url
        self.user = user

    @classmethod
    def _parse_user(cls, user):
        return User.de_json(user) if user else None

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        type = data.get('type')
        offset = data.get('offset')
        length = data.get('length')
        url = data.get('url')
        user = cls._parse_user(data.get('user'))

        return MessageEntity(data, type, offset, length, url, user)


class MessageEntityType:
    MENTION = 'mention'  # @username
    HASHTAG = 'hashtag'
    BOT_COMMAND = 'bot_command'
    URL = 'url'
    EMAIL = 'email'
    BOLD = 'bold'  # bold text
    ITALIC = 'italic'  # italic text
    CODE = 'code'  # monowidth string
    PRE = 'pre'  # monowidth block
    TEXT_LINK = 'text_link'  # for clickable text URLs
    TEXT_MENTION = 'text_mention'  # for users without usernames
