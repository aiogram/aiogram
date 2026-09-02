from typing import Annotated, TypeAlias

from pydantic import Field

from .owned_gift_regular import OwnedGiftRegular
from .owned_gift_unique import OwnedGiftUnique

OwnedGiftUnion: TypeAlias = Annotated[
    OwnedGiftRegular | OwnedGiftUnique, Field(discriminator="type")
]
