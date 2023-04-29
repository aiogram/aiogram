from .base import TelegramObject


class BotName(TelegramObject):
    """
    This object represents the bot's name.

    Source: https://core.telegram.org/bots/api#botname
    """

    name: str
    """The bot's name"""
