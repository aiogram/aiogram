from . import base, fields


class BotDescription(base.TelegramObject):
    """
    This object represents the bot's description.

    https://core.telegram.org/bots/api#botdescription
    """
    description: base.String = fields.Field()
