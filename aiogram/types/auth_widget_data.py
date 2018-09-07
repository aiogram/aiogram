from __future__ import annotations

from aiohttp import web

from . import base
from . import fields


class AuthWidgetData(base.TelegramObject):
    id: base.Integer = fields.Field()
    first_name: base.String = fields.Field()
    last_name: base.String = fields.Field()
    username: base.String = fields.Field()
    photo_url: base.String = fields.Field()
    auth_date: base.String = fields.DateTimeField()
    hash: base.String = fields.Field()

    @classmethod
    def parse(cls, request: web.Request) -> AuthWidgetData:
        """
        Parse request as Telegram auth widget data.

        :param request:
        :return: :obj:`AuthWidgetData`
        :raise: :obj:`aiohttp.web.HTTPBadRequest`
        """
        try:
            query = dict(request.query)
            query['id'] = int(query['id'])
            query['auth_date'] = int(query['auth_date'])
            widget = AuthWidgetData(**query)
        except (ValueError, KeyError):
            raise web.HTTPBadRequest(text='Invalid auth data')
        else:
            return widget

    def validate(self):
        return self.bot.check_auth_widget(self.to_python())

    @property
    def full_name(self):
        result = self.first_name
        if self.last_name:
            result += ' '
            result += self.last_name
        return result

    def __hash__(self):
        return self.id
