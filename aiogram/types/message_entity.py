import sys

from . import base, fields
from .user import User
from ..utils import helper, markdown
from ..utils.deprecated import deprecated


class MessageEntity(base.TelegramObject):
    """
    This object represents one special entity in a text message. For example, hashtags, usernames, URLs, etc.

    https://core.telegram.org/bots/api#messageentity
    """

    type: base.String = fields.Field()
    offset: base.Integer = fields.Field()
    length: base.Integer = fields.Field()
    url: base.String = fields.Field()
    user: User = fields.Field(base=User)
    language: base.String = fields.Field()
    custom_emoji_id: base.String = fields.Field()

    def __init__(
            self,
            type: base.String,
            offset: base.Integer,
            length: base.Integer,
            url: base.String = None,
            user: User = None,
            language: base.String = None,
            custom_emoji_id: base.String = None,
            **kwargs
    ):
        super().__init__(
            type=type,
            offset=offset,
            length=length,
            url=url,
            user=user,
            language=language,
            custom_emoji_id=custom_emoji_id,
            **kwargs
        )

    def get_text(self, text):
        """
        Get value of entity

        :param text: full text
        :return: part of text
        """
        if sys.maxunicode == 0xFFFF:
            return text[self.offset: self.offset + self.length]

        entity_text = (
            text.encode("utf-16-le") if not isinstance(text, bytes) else text
        )
        entity_text = entity_text[self.offset * 2: (self.offset + self.length) * 2]
        return entity_text.decode("utf-16-le")

    @deprecated(
        "This method doesn't work with nested entities and will be removed in aiogram 3.0"
    )
    def parse(self, text, as_html=True):
        """
        Get entity value with markup

        :param text: original text
        :param as_html: as html?
        :return: entity text with markup
        """
        if not text:
            return text
        entity_text = self.get_text(text)

        if self.type == MessageEntityType.BOLD:
            method = markdown.hbold if as_html else markdown.bold
            return method(entity_text)
        if self.type == MessageEntityType.ITALIC:
            method = markdown.hitalic if as_html else markdown.italic
            return method(entity_text)
        if self.type == MessageEntityType.SPOILER:
            method = markdown.spoiler if as_html else markdown.hspoiler
            return method(entity_text)
        if self.type == MessageEntityType.PRE:
            method = markdown.hpre if as_html else markdown.pre
            return method(entity_text)
        if self.type == MessageEntityType.CODE:
            method = markdown.hcode if as_html else markdown.code
            return method(entity_text)
        if self.type == MessageEntityType.URL:
            method = markdown.hlink if as_html else markdown.link
            return method(entity_text, entity_text)
        if self.type == MessageEntityType.TEXT_LINK:
            method = markdown.hlink if as_html else markdown.link
            return method(entity_text, self.url)
        if self.type == MessageEntityType.TEXT_MENTION and self.user:
            return self.user.get_mention(entity_text, as_html=as_html)
        if self.type == MessageEntityType.CUSTOM_EMOJI and self.user:
            return entity_text

        return entity_text


class MessageEntityType(helper.Helper):
    """
    List of entity types

    :key: MENTION
    :key: HASHTAG
    :key: CASHTAG
    :key: BOT_COMMAND
    :key: URL
    :key: EMAIL
    :key: PHONE_NUMBER
    :key: BOLD
    :key: ITALIC
    :key: UNDERLINE
    :key: STRIKETHROUGH
    :key: SPOILER
    :key: CODE
    :key: PRE
    :key: TEXT_LINK
    :key: TEXT_MENTION
    :key: CUSTOM_EMOJI
    """

    mode = helper.HelperMode.snake_case

    MENTION = helper.Item()  # mention - @username
    HASHTAG = helper.Item()  # hashtag
    CASHTAG = helper.Item()  # cashtag
    BOT_COMMAND = helper.Item()  # bot_command
    URL = helper.Item()  # url
    EMAIL = helper.Item()  # email
    PHONE_NUMBER = helper.Item()  # phone_number
    BOLD = helper.Item()  # bold -  bold text
    ITALIC = helper.Item()  # italic -  italic text
    UNDERLINE = helper.Item()  # underline
    STRIKETHROUGH = helper.Item()  # strikethrough
    SPOILER = helper.Item()  # spoiler
    CODE = helper.Item()  # code - monowidth string
    PRE = helper.Item()  # pre - monowidth block
    TEXT_LINK = helper.Item()  # text_link -  for clickable text URLs
    TEXT_MENTION = helper.Item()  # text_mention -  for users without usernames
    CUSTOM_EMOJI = helper.Item()  # custom_emoji
