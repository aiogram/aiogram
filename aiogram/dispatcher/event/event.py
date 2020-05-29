from __future__ import annotations

from typing import Any, Callable, List

from .handler import CallbackType, HandlerObject, HandlerType


class EventObserver:
    """
    Simple events observer
    """

    def __init__(self) -> None:
        self.handlers: List[HandlerObject] = []

    def register(self, callback: HandlerType) -> None:
        """
        Register callback with filters
        """
        self.handlers.append(HandlerObject(callback=callback))

    async def trigger(self, *args: Any, **kwargs: Any) -> None:
        """
        Propagate event to handlers.
        Handler will be called when all its filters is pass.
        """
        for handler in self.handlers:
            await handler.call(*args, **kwargs)

    def __call__(self) -> Callable[[CallbackType], CallbackType]:
        """
        Decorator for registering event handlers
        """

        def wrapper(callback: CallbackType) -> CallbackType:
            self.register(callback)
            return callback

        return wrapper
