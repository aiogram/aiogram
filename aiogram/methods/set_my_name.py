from typing import Optional

from .base import TelegramMethod


class SetMyName(TelegramMethod[bool]):
    """
    Use this method to change the bot's name. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setmyname
    """

    __returning__ = bool
    __api_method__ = "setMyName"

    name: Optional[str] = None
    """New bot name; 0-64 characters. Pass an empty string to remove the dedicated name for the given language."""
    language_code: Optional[str] = None
    """A two-letter ISO 639-1 language code. If empty, the name will be shown to all users for whose language there is no dedicated name."""
