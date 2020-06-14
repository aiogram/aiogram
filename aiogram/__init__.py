from .api import methods, types
from .api.client import session
from .api.client.bot import Bot
from .dispatcher import filters, handler
from .dispatcher.dispatcher import Dispatcher
from .dispatcher.middlewares.base import BaseMiddleware
from .dispatcher.router import Router

try:
    import uvloop as _uvloop

    _uvloop.install()
except ImportError:  # pragma: no cover
    _uvloop = None


__all__ = (
    "__api_version__",
    "__version__",
    "types",
    "methods",
    "Bot",
    "session",
    "Dispatcher",
    "Router",
    "BaseMiddleware",
    "filters",
    "handler",
)

__version__ = "3.0.0a5"
__api_version__ = "4.9"
