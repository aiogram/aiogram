from __future__ import annotations

from typing import Optional

from .base import TelegramMethod


class SetMyShortDescription(TelegramMethod[bool]):
    """
    Use this method to change the bot's short description, which is shown on the bot's profile page and is sent together with the link when users share the bot. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setmyshortdescription
    """

    __returning__ = bool
    __api_method__ = "setMyShortDescription"

    short_description: Optional[str] = None
    """New short description for the bot; 0-120 characters. Pass an empty string to remove the dedicated short description for the given language."""
    language_code: Optional[str] = None
    """A two-letter ISO 639-1 language code. If empty, the short description will be applied to all users for whose language there is no dedicated short description."""
