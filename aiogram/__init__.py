import asyncio
import os

from .bot import Bot
from .dispatcher import Dispatcher

try:
    import uvloop
except ImportError:
    uvloop = None
else:
    if 'DISABLE_UVLOOP' not in os.environ:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

__version__ = '2.0.dev1'
__api_version__ = '3.6'
