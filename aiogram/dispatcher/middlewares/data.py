from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from typing_extensions import NotRequired

if TYPE_CHECKING:
    from aiogram import Bot, Dispatcher, Router
    from aiogram.dispatcher.event.handler import HandlerObject
    from aiogram.dispatcher.middlewares.user_context import EventContext
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import BaseStorage
    from aiogram.types import Chat, Update, User
    from aiogram.utils.i18n import I18n, I18nMiddleware


class DispatcherData(TypedDict, total=False):
    """
    Dispatcher and bot related data.
    """

    dispatcher: Dispatcher
    bot: Bot
    bots: list[Bot]
    event_update: Update
    event_router: Router
    handler: NotRequired[HandlerObject]


class UserContextData(TypedDict, total=False):
    """
    Event context related data about user and chat.
    """

    event_context: EventContext
    event_from_user: NotRequired[User]
    event_chat: NotRequired[Chat]  # Deprecated
    event_thread_id: NotRequired[int]  # Deprecated
    event_business_connection_id: NotRequired[str]  # Deprecated


class FSMData(TypedDict, total=False):
    """
    FSM related data.
    """

    fsm_storage: BaseStorage
    state: NotRequired[FSMContext]
    raw_state: NotRequired[str | None]


class I18nData(TypedDict, total=False):
    """
    I18n related data.

    Is not included by default, you need to add it to your own Data class if you need it.
    """

    i18n: I18n
    i18n_middleware: I18nMiddleware


class MiddlewareData(
    DispatcherData,
    UserContextData,
    FSMData,
    # I18nData, # Disabled by default, add it if you need it to your own Data class.
    total=False,
):
    """
    Data passed to the handler by the middlewares.

    You can add your own data by extending this class.
    """
