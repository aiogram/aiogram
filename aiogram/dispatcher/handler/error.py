from abc import ABC

from aiogram.dispatcher.handler.base import BaseHandler


class ErrorHandler(BaseHandler[Exception], ABC):
    """
    Base class for errors handlers
    """
