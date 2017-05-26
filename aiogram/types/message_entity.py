from . import Deserializable
from .user import User


class MessageEntity(Deserializable):
    __slots__ = ('type', 'offset', 'length', 'url', 'user')

    def __init__(self, type, offset, length, url, user):
        self.type = type
        self.offset = offset
        self.length = length
        self.url = url
        self.user = user

    @classmethod
    def _parse_user(cls, user):
        return User.de_json(user) if user else None

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        type = raw_data.get('type')
        offset = raw_data.get('offset')
        length = raw_data.get('length')
        url = raw_data.get('url')
        user = cls._parse_user(raw_data.get('user'))

        return MessageEntity(type, offset, length, url, user)


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
