from aiogram.types import TelegramObject


class BotDescription(TelegramObject):
    """
    This object represents the bot's description.

    Source: https://core.telegram.org/bots/api#botdescription
    """

    description: str
    """The bot's description"""
