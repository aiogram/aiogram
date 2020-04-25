import asyncio
import os

from . import bot
from . import contrib
from . import dispatcher
from . import types
from . import utils
from .bot import Bot
from .dispatcher import Dispatcher
from .dispatcher import filters
from .dispatcher import middlewares
from .utils import exceptions, executor, helper, markdown as md

try:
    import uvloop
except ImportError:
    uvloop = None
else:
    if 'DISABLE_UVLOOP' not in os.environ:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

__all__ = [
    'Bot',
    'Dispatcher',
    '__api_version__',
    '__version__',
    'bot',
    'contrib',
    'dispatcher',
    'exceptions',
    'executor',
    'filters',
    'helper',
    'md',
    'middlewares',
    'types',
    'utils'
]

__version__ = '2.8'
__api_version__ = '4.8'
