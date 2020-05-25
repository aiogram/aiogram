from pkg_resources import get_distribution

from .api import methods, types
from .api.client import session
from .api.client.bot import Bot
from .dispatcher import filters, handler
from .dispatcher.dispatcher import Dispatcher
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
    "filters",
    "handler",
)

__version__ = get_distribution(dist=__package__).version
__api_version__ = "4.8"
