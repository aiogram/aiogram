from typing import Annotated, TypeAlias

from pydantic import Field

from .emoji_type_custom_emoji import EmojiTypeCustomEmoji
from .emoji_type_emoji import EmojiTypeEmoji

EmojiTypeUnion: TypeAlias = Annotated[
    EmojiTypeEmoji | EmojiTypeCustomEmoji, Field(discriminator="type")
]
