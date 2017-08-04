from .utils.versions import Version, Stage
from .bot import Bot


VERSION = Version(0, 3, 5, stage=Stage.DEV, build=0)

__version__ = VERSION.version
