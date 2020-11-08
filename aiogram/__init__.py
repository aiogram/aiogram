import sys

if sys.version_info < (3, 7):
    raise ImportError('Your Python version {0} is not supported by aiogram, please install '
                      'Python 3.7+'.format('.'.join(map(str, sys.version_info[:3]))))

import asyncio
import os

from . import bot, contrib, dispatcher, types, utils
from .bot import Bot
from .dispatcher import Dispatcher, filters, middlewares
from .utils import exceptions, executor, helper
from .utils import markdown as md

try:
    import uvloop
except ImportError:
    uvloop = None
else:
    if 'DISABLE_UVLOOP' not in os.environ:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

__all__ = (
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
    'utils',
)

__version__ = '2.11'
__api_version__ = '5.0'
