from aiogram.dispatcher.flags import FlagGenerator

from .client import session
from .client.bot import Bot
from .dispatcher.dispatcher import Dispatcher
from .dispatcher.middlewares.base import BaseMiddleware
from .dispatcher.router import Router
from .utils.magic_filter import MagicFilter
from .utils.text_decorations import html_decoration as html
from .utils.text_decorations import markdown_decoration as md

try:
    import uvloop as _uvloop

    _uvloop.install()
except ImportError:  # pragma: no cover
    pass

F = MagicFilter()
flags = FlagGenerator()

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
    "F",
    "html",
    "md",
    "flags",
)

__version__ = "3.0.0b6"
__api_version__ = "6.3"
