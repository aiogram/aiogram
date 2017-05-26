from . import Deserializable, deserialize
from .user import User


class MessageEntity(Deserializable):
    def __init__(self, type, offset, length, url, user):
        self.type: str = type
        self.offset: int = offset
        self.length: int = length
        self.url: str = url
        self.user: User = user

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        type = raw_data.get('type')
        offset = raw_data.get('offset')
        length = raw_data.get('length')
        url = raw_data.get('url')
        user = User.deserialize(raw_data.get('user'))

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
