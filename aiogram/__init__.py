# from .bot import Bot
from .utils.versions import Version, Stage

VERSION = Version(1, 0, 0, stage=Stage.DEV, build=0)

__version__ = VERSION.version
