from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, Optional, Set, cast

try:
    from babel import Locale
except ImportError:  # pragma: no cover
    Locale = None

from aiogram import BaseMiddleware, Router
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import TelegramObject, User
from aiogram.utils.i18n.context import ctx_i18n
from aiogram.utils.i18n.core import I18n


class I18nMiddleware(BaseMiddleware, ABC):
    def __init__(
        self,
        i18n: I18n,
        i18n_key: Optional[str] = "i18n",
        middleware_key: str = "i18n_middleware",
    ) -> None:
        self.i18n = i18n
        self.i18n_key = i18n_key
        self.middleware_key = middleware_key

    def setup(
        self: BaseMiddleware, router: Router, exclude: Optional[Set[str]] = None
    ) -> BaseMiddleware:
        if exclude is None:
            exclude = set()
        exclude_events = {"update", "error", *exclude}
        for event_name, observer in router.observers.items():
            if event_name in exclude_events:
                continue
            observer.outer_middleware(self)
        return self

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        self.i18n.current_locale = await self.get_locale(event=event, data=data)

        if self.i18n_key:
            data[self.i18n_key] = self.i18n
        if self.middleware_key:
            data[self.middleware_key] = self
        token = ctx_i18n.set(self.i18n)
        try:
            return await handler(event, data)
        finally:
            ctx_i18n.reset(token)

    @abstractmethod
    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        pass


class SimpleI18nMiddleware(I18nMiddleware):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if Locale is None:  # pragma: no cover
            raise RuntimeError(
                f"{type(self).__name__} can be used only when Babel installed\n"
                "Just install Babel (`pip install Babel`) "
                "or aiogram with i18n support (`pip install aiogram[i18n]`)"
            )

    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        if Locale is None:  # pragma: no cover
            raise RuntimeError(
                f"{type(self).__name__} can be used only when Babel installed\n"
                "Just install Babel (`pip install Babel`) "
                "or aiogram with i18n support (`pip install aiogram[i18n]`)"
            )

        event_from_user: Optional[User] = data.get("event_from_user", None)
        if event_from_user is None:
            return self.i18n.locale
        locale = Locale.parse(event_from_user.language_code, sep="-")
        if locale.language not in self.i18n.available_locales:
            return self.i18n.locale
        return cast(str, locale.language)


class ConstI18nMiddleware(I18nMiddleware):
    def __init__(self, locale: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.locale = locale

    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        return self.locale


class FSMI18nMiddleware(SimpleI18nMiddleware):
    def __init__(self, *args: Any, key: str = "locale", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.key = key

    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        fsm_context: Optional[FSMContext] = data.get("state")
        locale = None
        if fsm_context:
            fsm_data = await fsm_context.get_data()
            locale = fsm_data.get(self.key, None)
        if not locale:
            locale = await super().get_locale(event=event, data=data)
            if fsm_context:
                await fsm_context.update_data(data={self.key: locale})
        return locale

    async def set_locale(self, state: FSMContext, locale: str) -> None:
        await state.update_data(data={self.key: locale})
        self.i18n.current_locale = locale
