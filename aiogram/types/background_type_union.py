from __future__ import annotations

from typing import Annotated, TypeAlias

from pydantic import Field

from .background_type_chat_theme import BackgroundTypeChatTheme
from .background_type_fill import BackgroundTypeFill
from .background_type_pattern import BackgroundTypePattern
from .background_type_wallpaper import BackgroundTypeWallpaper

BackgroundTypeUnion: TypeAlias = Annotated[
    BackgroundTypeFill | BackgroundTypeWallpaper | BackgroundTypePattern | BackgroundTypeChatTheme,
    Field(discriminator="type"),
]
