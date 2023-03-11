from __future__ import annotations

from typing import TYPE_CHECKING, Union

from .base import TelegramMethod


class SetChatAdministratorCustomTitle(TelegramMethod[bool]):
    """
    Use this method to set a custom title for an administrator in a supergroup promoted by the bot. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setchatadministratorcustomtitle
    """

    __returning__ = bool
    __api_method__ = "setChatAdministratorCustomTitle"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
    user_id: int
    """Unique identifier of the target user"""
    custom_title: str
    """New custom title for the administrator; 0-16 characters, emoji are not allowed"""
