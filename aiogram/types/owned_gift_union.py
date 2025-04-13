from typing import Union

from .owned_gift_regular import OwnedGiftRegular
from .owned_gift_unique import OwnedGiftUnique

OwnedGiftUnion = Union[OwnedGiftRegular, OwnedGiftUnique]
