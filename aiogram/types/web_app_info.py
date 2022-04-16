from . import base
from . import fields


class WebAppInfo(base.TelegramObject):
    """
    Contains information about a Web App.

    Source: https://core.telegram.org/bots/api#webappinfo
    """
    url: base.String = fields.Field()
