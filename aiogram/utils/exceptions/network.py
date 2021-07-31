from aiogram.utils.exceptions.base import TelegramAPIError


class NetworkError(TelegramAPIError):
    pass


class EntityTooLarge(NetworkError):
    url = "https://core.telegram.org/bots/api#sending-files"
