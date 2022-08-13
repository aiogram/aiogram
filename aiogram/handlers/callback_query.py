from abc import ABC
from typing import Optional

from aiogram.handlers import BaseHandler
from aiogram.types import CallbackQuery, Message, User


class CallbackQueryHandler(BaseHandler[CallbackQuery], ABC):
    """
    There is base class for callback query handlers.

    Example:
        .. code-block:: python

            from aiogram.handlers import CallbackQueryHandler

            ...

            @router.callback_query()
            class MyHandler(CallbackQueryHandler):
                async def handle(self) -> Any: ...
    """

    @property
    def from_user(self) -> User:
        """
        Is alias for `event.from_user`
        """
        return self.event.from_user

    @property
    def message(self) -> Optional[Message]:
        """
        Is alias for `event.message`
        """
        return self.event.message

    @property
    def callback_data(self) -> Optional[str]:
        """
        Is alias for `event.data`
        """
        return self.event.data
