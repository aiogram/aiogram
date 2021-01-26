from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict

from ...types import Update
from ..event.bases import UNHANDLED, CancelHandler, SkipHandler
from .base import BaseMiddleware

if TYPE_CHECKING:  # pragma: no cover
    from ..router import Router


class ErrorsMiddleware(BaseMiddleware[Update]):
    def __init__(self, router: Router):
        self.router = router

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except (SkipHandler, CancelHandler):  # pragma: no cover
            raise
        except Exception as e:
            for router in self.router.chain:
                observer = router.observers["error"]
                response = await observer.trigger(event, exception=e, **data)
                if response is not UNHANDLED:
                    return response
            raise
