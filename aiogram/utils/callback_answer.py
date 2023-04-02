from typing import Any, Awaitable, Callable, Dict, Optional, Union

from aiogram import BaseMiddleware, loggers
from aiogram.dispatcher.flags import get_flag
from aiogram.exceptions import CallbackAnswerException
from aiogram.methods import AnswerCallbackQuery
from aiogram.types import CallbackQuery, TelegramObject


class CallbackAnswer:
    def __init__(
        self,
        answered: bool,
        disabled: bool = False,
        text: Optional[str] = None,
        show_alert: Optional[bool] = None,
        url: Optional[str] = None,
        cache_time: Optional[int] = None,
    ) -> None:
        """
        Callback answer configuration

        :param answered: this request is already answered by middleware
        :param disabled: answer will not be performed
        :param text: answer with text
        :param show_alert: show alert
        :param url: game url
        :param cache_time: cache answer for some time
        """
        self._answered = answered
        self._disabled = disabled
        self._text = text
        self._show_alert = show_alert
        self._url = url
        self._cache_time = cache_time

    def disable(self) -> None:
        """
        Deactivate answering for this handler
        """
        self.disabled = True

    @property
    def disabled(self) -> bool:
        """Indicates that automatic answer is disabled in this handler"""
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        if self._answered:
            raise CallbackAnswerException("Can't change disabled state after answer")
        self._disabled = value

    @property
    def answered(self) -> bool:
        """
        Indicates that request is already answered by middleware
        """
        return self._answered

    @property
    def text(self) -> Optional[str]:
        """
        Response text
        :return:
        """
        return self._text

    @text.setter
    def text(self, value: Optional[str]) -> None:
        if self._answered:
            raise CallbackAnswerException("Can't change text after answer")
        self._text = value

    @property
    def show_alert(self) -> Optional[bool]:
        """
        Whether to display an alert
        """
        return self._show_alert

    @show_alert.setter
    def show_alert(self, value: Optional[bool]) -> None:
        if self._answered:
            raise CallbackAnswerException("Can't change show_alert after answer")
        self._show_alert = value

    @property
    def url(self) -> Optional[str]:
        """
        Game url
        """
        return self._url

    @url.setter
    def url(self, value: Optional[str]) -> None:
        if self._answered:
            raise CallbackAnswerException("Can't change url after answer")
        self._url = value

    @property
    def cache_time(self) -> Optional[int]:
        """
        Response cache time
        """
        return self._cache_time

    @cache_time.setter
    def cache_time(self, value: Optional[int]) -> None:
        if self._answered:
            raise CallbackAnswerException("Can't change cache_time after answer")
        self._cache_time = value

    def __str__(self) -> str:
        args = ", ".join(
            f"{k}={v!r}"
            for k, v in {
                "answered": self.answered,
                "disabled": self.disabled,
                "text": self.text,
                "show_alert": self.show_alert,
                "url": self.url,
                "cache_time": self.cache_time,
            }.items()
            if v is not None
        )
        return f"{type(self).__name__}({args})"


class CallbackAnswerMiddleware(BaseMiddleware):
    def __init__(
        self,
        pre: bool = False,
        text: Optional[str] = None,
        show_alert: Optional[bool] = None,
        url: Optional[str] = None,
        cache_time: Optional[int] = None,
    ) -> None:
        """
        Inner middleware for callback query handlers, can be useful in bots with a lot of callback
        handlers to automatically take answer to all requests

        :param pre: send answer before execute handler
        :param text: answer with text
        :param show_alert: show alert
        :param url: game url
        :param cache_time: cache answer for some time
        """
        self.pre = pre
        self.text = text
        self.show_alert = show_alert
        self.url = url
        self.cache_time = cache_time

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)

        callback_answer = data["callback_answer"] = self.construct_callback_answer(
            properties=get_flag(data, "callback_answer")
        )

        if not callback_answer.disabled and callback_answer.answered:
            await self.answer(event, callback_answer)
        try:
            return await handler(event, data)
        finally:
            if not callback_answer.disabled and not callback_answer.answered:
                await self.answer(event, callback_answer)

    def construct_callback_answer(
        self, properties: Optional[Union[Dict[str, Any], bool]]
    ) -> CallbackAnswer:
        pre, disabled, text, show_alert, url, cache_time = (
            self.pre,
            False,
            self.text,
            self.show_alert,
            self.url,
            self.cache_time,
        )
        if isinstance(properties, dict):
            pre = properties.get("pre", pre)
            disabled = properties.get("disabled", disabled)
            text = properties.get("text", text)
            show_alert = properties.get("show_alert", show_alert)
            url = properties.get("url", url)
            cache_time = properties.get("cache_time", cache_time)

        return CallbackAnswer(
            answered=pre,
            disabled=disabled,
            text=text,
            show_alert=show_alert,
            url=url,
            cache_time=cache_time,
        )

    def answer(self, event: CallbackQuery, callback_answer: CallbackAnswer) -> AnswerCallbackQuery:
        loggers.middlewares.info("Answer to callback query id=%s", event.id)
        return event.answer(
            text=callback_answer.text,
            show_alert=callback_answer.show_alert,
            url=callback_answer.url,
            cache_time=callback_answer.cache_time,
        )
