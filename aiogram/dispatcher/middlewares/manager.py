from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List
from warnings import warn

from .abstract import AbstractMiddleware
from .types import MiddlewareStep, UpdateType

if TYPE_CHECKING:  # pragma: no cover
    from aiogram.dispatcher.router import Router


class MiddlewareManager:
    """
    Middleware manager.
    """

    def __init__(self, router: Router) -> None:
        self.router = router
        self.middlewares: List[AbstractMiddleware] = []

    def setup(self, middleware: AbstractMiddleware, _stack_level: int = 1) -> AbstractMiddleware:
        """
        Setup middleware

        :param middleware:
        :param _stack_level:
        :return:
        """
        if not isinstance(middleware, AbstractMiddleware):
            raise TypeError(
                f"`middleware` should be instance of BaseMiddleware, not {type(middleware)}"
            )
        if middleware.configured:
            if middleware.manager is self:
                warn(
                    f"Middleware {middleware} is already configured for this Router "
                    "That's mean re-installing of this middleware has no effect.",
                    category=RuntimeWarning,
                    stacklevel=_stack_level + 1,
                )
                return middleware
            raise ValueError(
                f"Middleware is already configured for another manager {middleware.manager} "
                f"in router {middleware.manager.router}!"
            )

        self.middlewares.append(middleware)
        middleware.setup(self)
        return middleware

    async def trigger(
        self,
        step: MiddlewareStep,
        event_name: str,
        event: UpdateType,
        data: Dict[str, Any],
        result: Any = None,
        reverse: bool = False,
    ) -> Any:
        """
        Call action to middlewares with args lilt.
        """
        middlewares = reversed(self.middlewares) if reverse else self.middlewares
        for middleware in middlewares:
            await middleware.trigger(
                step=step, event_name=event_name, event=event, data=data, result=result
            )

    def __contains__(self, item: AbstractMiddleware) -> bool:
        return item in self.middlewares
