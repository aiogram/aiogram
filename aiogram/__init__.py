from .bot import Bot
from .utils.versions import Version, Stage

VERSION = Version(0, 4, stage=Stage.FINAL, build=0)

__version__ = VERSION.version
