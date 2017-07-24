from .utils.versions import Version, Stage
from .bot import Bot


VERSION = Version(0, 3, 2, stage=Stage.FINAL, build=3)

__version__ = VERSION.version
