from . import base
from . import fields


class WebAppData(base.TelegramObject):
    """
    Contains data sent from a Web App to the bot.

    Source: https://core.telegram.org/bots/api#webappdata
    """
    data: str = fields.Field()
    button_text: str = fields.Field()
