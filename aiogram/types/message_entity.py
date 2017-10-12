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

    def _apply(self, text, func):
        return text[:self.offset] + \
               func(text[self.offset:self.offset + self.length]) + \
               text[self.offset + self.length:]

    def apply_md(self, text):
        """
        Apply entity for text as Markdown

        :param text:
        :return:
        """
        if self.type == MessageEntityType.BOLD:
            return self._apply(text, markdown.bold)
        elif self.type == MessageEntityType.ITALIC:
            return self._apply(text, markdown.italic)
        elif self.type == MessageEntityType.PRE:
            return self._apply(text, markdown.pre)
        elif self.type == MessageEntityType.CODE:
            return self._apply(text, markdown.code)
        elif self.type == MessageEntityType.URL:
            return self._apply(text, lambda url: markdown.link(url, url))
        elif self.type == MessageEntityType.TEXT_LINK:
            return self._apply(text, lambda url: markdown.link(url, self.url))
        return text

    def apply_html(self, text):
        """
        Apply entity for text as HTML

        :param text:
        :return:
        """
        if self.type == MessageEntityType.BOLD:
            return self._apply(text, markdown.hbold)
        elif self.type == MessageEntityType.ITALIC:
            return self._apply(text, markdown.hitalic)
        elif self.type == MessageEntityType.PRE:
            return self._apply(text, markdown.hpre)
        elif self.type == MessageEntityType.CODE:
            return self._apply(text, markdown.hcode)
        elif self.type == MessageEntityType.URL:
            return self._apply(text, lambda url: markdown.hlink(url, url))
        elif self.type == MessageEntityType.TEXT_LINK:
            return self._apply(text, lambda url: markdown.hlink(url, self.url))
        return text


class MessageEntityType(helper.Helper):
    """
    List of entity types

    :key: MENTION
    :key: HASHTAG
    :key: BOT_COMMAND
    :key: URL
    :key: EMAIL
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
    BOT_COMMAND = helper.Item()  # bot_command
    URL = helper.Item()  # url
    EMAIL = helper.Item()  # email
    BOLD = helper.Item()  # bold -  bold text
    ITALIC = helper.Item()  # italic -  italic text
    CODE = helper.Item()  # code -  monowidth string
    PRE = helper.Item()  # pre -  monowidth block
    TEXT_LINK = helper.Item()  # text_link -  for clickable text URLs
    TEXT_MENTION = helper.Item()  # text_mention -  for users without usernames
