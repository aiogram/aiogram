from .client import session
from .client.bot import Bot
from .dispatcher import filters, handler
from .dispatcher.dispatcher import Dispatcher
from .dispatcher.flags.flag import FlagGenerator
from .dispatcher.middlewares.base import BaseMiddleware
from .dispatcher.router import Router
from .utils.magic_filter import MagicFilter
from .utils.text_decorations import html_decoration as _html_decoration
from .utils.text_decorations import markdown_decoration as _markdown_decoration

try:
    import uvloop as _uvloop

    _uvloop.install()
except ImportError:  # pragma: no cover
    pass

F = MagicFilter()
html = _html_decoration
md = _markdown_decoration
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
    "filters",
    "handler",
    "F",
    "html",
    "md",
    "flags",
)

__version__ = "3.0.0b2"
__api_version__ = "5.7"
