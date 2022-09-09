from __future__ import annotations

from typing import Optional

import babel

from . import base
from . import fields
from ..utils import markdown
from ..utils.deprecated import deprecated


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
    is_premium: base.Boolean = fields.Field()
    added_to_attachment_menu: base.Boolean = fields.Field()
    can_join_groups: base.Boolean = fields.Field()
    can_read_all_group_messages: base.Boolean = fields.Field()
    supports_inline_queries: base.Boolean = fields.Field()

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
    def locale(self) -> Optional[babel.core.Locale]:
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
    def url(self) -> str:
        return f"tg://user?id={self.id}"

    def get_mention(self, name: Optional[str] = None, as_html: Optional[bool] = None) -> str:
        if as_html is None and self.bot.parse_mode and self.bot.parse_mode.lower() == 'html':
            as_html = True

        if name is None:
            name = self.full_name
        if as_html:
            return markdown.hlink(name, self.url)
        return markdown.link(name, self.url)

    @deprecated(
        '`get_user_profile_photos` is outdated, please use `get_profile_photos`',
        stacklevel=3
    )
    async def get_user_profile_photos(self, offset=None, limit=None):
        return await self.bot.get_user_profile_photos(self.id, offset, limit)

    async def get_profile_photos(self, offset=None, limit=None):
        return await self.bot.get_user_profile_photos(self.id, offset, limit)

    def __hash__(self):
        return self.id

    def __int__(self):
        return self.id
