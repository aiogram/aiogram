import sys

from . import base
from . import fields
from .user import User
from ..utils import helper, markdown


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

    def get_text(self, text):
        """
        Get value of entity

        :param text: full text
        :return: part of text
        """
        if sys.maxunicode == 0xffff:
            return text[self.offset:self.offset + self.length]

        if not isinstance(text, bytes):
            entity_text = text.encode('utf-16-le')
        else:
            entity_text = text

        entity_text = entity_text[self.offset * 2:(self.offset + self.length) * 2]
        return entity_text.decode('utf-16-le')

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
            if as_html:
                return markdown.hbold(entity_text)
            return markdown.bold(entity_text)
        elif self.type == MessageEntityType.ITALIC:
            if as_html:
                return markdown.hitalic(entity_text)
            return markdown.italic(entity_text)
        elif self.type == MessageEntityType.PRE:
            if as_html:
                return markdown.hpre(entity_text)
            return markdown.pre(entity_text)
        elif self.type == MessageEntityType.CODE:
            if as_html:
                return markdown.hcode(entity_text)
            return markdown.code(entity_text)
        elif self.type == MessageEntityType.URL:
            if as_html:
                return markdown.hlink(entity_text, entity_text)
            return markdown.link(entity_text, entity_text)
        elif self.type == MessageEntityType.TEXT_LINK:
            if as_html:
                return markdown.hlink(entity_text, self.url)
            return markdown.link(entity_text, self.url)
        elif self.type == MessageEntityType.TEXT_MENTION and self.user:
            return self.user.get_mention(entity_text)
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
    :key: CODE
    :key: PRE
    :key: TEXT_LINK
    :key: TEXT_MENTION
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
    CODE = helper.Item()  # code -  monowidth string
    PRE = helper.Item()  # pre -  monowidth block
    TEXT_LINK = helper.Item()  # text_link -  for clickable text URLs
    TEXT_MENTION = helper.Item()  # text_mention -  for users without usernames
