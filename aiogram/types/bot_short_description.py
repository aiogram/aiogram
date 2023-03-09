from . import base, fields


class BotShortDescription(base.TelegramObject):
    """
    This object represents the bot's short description.

    https://core.telegram.org/bots/api#botshortdescription
    """
    short_description: base.String = fields.Field()
