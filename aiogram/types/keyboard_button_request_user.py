from typing import Optional

from aiogram.types import TelegramObject


class KeyboardButtonRequestUser(TelegramObject):
    """
    This object defines the criteria used to request a suitable user. The identifier of the selected user will be shared with the bot when the corresponding button is pressed.

    Source: https://core.telegram.org/bots/api#keyboardbuttonrequestuser
    """

    request_id: int
    """Signed 32-bit identifier of the request, which will be received back in the :class:`aiogram.types.user_shared.UserShared` object. Must be unique within the message"""
    user_is_bot: Optional[bool] = None
    """*Optional*. Pass :code:`True` to request a bot, pass :code:`False` to request a regular user. If not specified, no additional restrictions are applied."""
    user_is_premium: Optional[bool] = None
    """*Optional*. Pass :code:`True` to request a premium user, pass :code:`False` to request a non-premium user. If not specified, no additional restrictions are applied."""
