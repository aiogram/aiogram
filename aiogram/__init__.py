from .api import methods, session, types
from .api.client.bot import Bot

__all__ = ["__api_version__", "__version__", "types", "methods", "Bot", "session"]

__version__ = "3.0dev.1"
__api_version__ = "4.4"
