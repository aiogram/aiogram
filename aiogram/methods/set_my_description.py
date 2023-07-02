from __future__ import annotations

from typing import Optional

from .base import TelegramMethod


class SetMyDescription(TelegramMethod[bool]):
    """
    Use this method to change the bot's description, which is shown in the chat with the bot if the chat is empty. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setmydescription
    """

    __returning__ = bool
    __api_method__ = "setMyDescription"

    description: Optional[str] = None
    """New bot description; 0-512 characters. Pass an empty string to remove the dedicated description for the given language."""
    language_code: Optional[str] = None
    """A two-letter ISO 639-1 language code. If empty, the description will be applied to all users for whose language there is no dedicated description."""
