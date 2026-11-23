from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Protocol

from aiogram.methods.base import TelegramType

if TYPE_CHECKING:
    from aiogram.client.bot import Bot
    from aiogram.client.session.base import BaseSession
    from aiogram.methods import TelegramMethod


class RequestContext(Generic[TelegramType]):
    """
    One API call as it passes through the request middlewares.

    :class:`~aiogram.client.session.base.BaseSession` creates one per call. Every middleware
    gets the same object: an outer one can change :attr:`method`, :attr:`timeout` or
    :attr:`attempt` before :meth:`next`, and inner ones see the change.
    """

    __slots__ = ("_chain", "_index", "_session", "attempt", "bot", "method", "timeout")

    def __init__(
        self,
        session: BaseSession,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,
    ) -> None:
        self.bot = bot
        #: The method to send; a middleware may replace it before :meth:`next`
        self.method = method
        #: Request timeout passed to :meth:`~aiogram.client.session.base.BaseSession.make_request`
        self.timeout = timeout
        #: Attempt number, starting at 1; a retrying middleware sets it before each :meth:`next`
        self.attempt = 1
        self._session = session
        self._chain = session.middleware.chain
        self._index = 0

    def _fork(
        self, bot: Bot, method: TelegramMethod[TelegramType]
    ) -> RequestContext[TelegramType]:
        """A copy at the same chain position, for one call of a 3.x ``make_request``."""
        fork = object.__new__(RequestContext)
        fork.bot = bot
        fork.method = method
        fork.timeout = self.timeout
        fork.attempt = self.attempt
        fork._session = self._session
        fork._chain = self._chain
        fork._index = self._index
        return fork

    async def next(self) -> TelegramType:
        """
        Run the rest of the chain, then the request itself.

        May be called again after it returns (a retry); concurrent calls on one context are
        not supported.
        """
        index = self._index
        if index == len(self._chain):
            return await self._session.make_request(self.bot, self.method, timeout=self.timeout)
        self._index = index + 1
        try:
            return await self._chain[index](self)
        finally:
            self._index = index


class RequestMiddlewareType(Protocol):  # pragma: no cover
    async def __call__(self, ctx: RequestContext[TelegramType]) -> TelegramType:
        pass


class NextRequestMiddlewareType(Protocol[TelegramType]):  # pragma: no cover
    """``make_request`` of a deprecated 3.x ``(make_request, bot, method)`` middleware."""

    async def __call__(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> TelegramType:
        pass


class BaseRequestMiddleware(ABC):
    """
    Generic middleware class
    """

    @abstractmethod
    async def __call__(self, ctx: RequestContext[TelegramType]) -> TelegramType:
        """
        Execute middleware

        :param ctx: the API call; :code:`await ctx.next()` continues the chain
        :return: the method's result
        """
