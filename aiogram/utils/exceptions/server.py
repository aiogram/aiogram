from aiogram.utils.exceptions.base import TelegramAPIError


class ServerError(TelegramAPIError):
    pass


class RestartingTelegram(ServerError):
    pass
