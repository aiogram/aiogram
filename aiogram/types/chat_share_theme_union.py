from typing import Annotated, TypeAlias

from pydantic import Field

from .chat_share_theme_emoji import ChatShareThemeEmoji
from .chat_share_theme_unique_gift import ChatShareThemeUniqueGift

ChatShareThemeUnion: TypeAlias = Annotated[
    ChatShareThemeEmoji | ChatShareThemeUniqueGift, Field(discriminator="type")
]
