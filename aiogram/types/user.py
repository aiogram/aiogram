from __future__ import annotations

import babel

from . import base
from . import fields
from ..utils import markdown


class User(base.TelegramObject):
    """
    This object represents a Telegram user or bot.

    https://core.telegram.org/bots/api#user
    """
    id: base.Integer = fields.Field()
    is_bot: base.Boolean = fields.Field()
    first_name: base.String = fields.Field()
    last_name: base.String = fields.Field()
    username: base.String = fields.Field()
    language_code: base.String = fields.Field()

    @property
    def full_name(self):
        """
        You can get full name of user.

        :return: str
        """
        full_name = self.first_name
        if self.last_name:
            full_name += ' ' + self.last_name
        return full_name

    @property
    def mention(self):
        """
        You can get user's username to mention him
        Full name will be returned if user has no username

        :return: str
        """
        if self.username:
            return '@' + self.username
        return self.full_name

    @property
    def locale(self) -> babel.core.Locale or None:
        """
        Get user's locale

        :return: :class:`babel.core.Locale`
        """
        if not self.language_code:
            return None
        if not hasattr(self, '_locale'):
            setattr(self, '_locale', babel.core.Locale.parse(self.language_code, sep='-'))
        return getattr(self, '_locale')

    @property
    def url(self):
        return f"tg://user?id={self.id}"

    def get_mention(self, name=None, as_html=None):
        if as_html is None and self.bot.parse_mode and self.bot.parse_mode.lower() == 'html':
            as_html = True

        if name is None:
            name = self.full_name
        if as_html:
            return markdown.hlink(name, self.url)
        return markdown.link(name, self.url)

    async def get_user_profile_photos(self, offset=None, limit=None):
        return await self.bot.get_user_profile_photos(self.id, offset, limit)

    def __hash__(self):
        return self.id

    def __int__(self):
        return self.id
