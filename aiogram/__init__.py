from .bot import Bot
from .utils.versions import Version, Stage

VERSION = Version(1, 0, 0, stage=Stage.DEV, build=0)
API_VERSION = Version(3, 4)

__version__ = VERSION.version
__api_version__ = API_VERSION.version
