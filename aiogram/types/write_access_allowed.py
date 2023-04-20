from typing import Optional

from aiogram.types import TelegramObject


class WriteAccessAllowed(TelegramObject):
    """
    This object represents a service message about a user allowing a bot added to the attachment menu to write messages. Currently holds no information.

    Source: https://core.telegram.org/bots/api#writeaccessallowed
    """

    web_app_name: Optional[str] = None
    """*Optional*. Name of the Web App which was launched from a link"""
