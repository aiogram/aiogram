from .bot import Bot
from .utils.versions import Version, Stage

VERSION = Version(0, 3, 5, stage=Stage.DEV, build=0)

__version__ = VERSION.version
