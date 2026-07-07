from __future__ import annotations

from typing import Annotated, TypeAlias

from pydantic import Field

from .reaction_type_custom_emoji import ReactionTypeCustomEmoji
from .reaction_type_emoji import ReactionTypeEmoji
from .reaction_type_paid import ReactionTypePaid

ReactionTypeUnion: TypeAlias = Annotated[
    ReactionTypeEmoji | ReactionTypeCustomEmoji | ReactionTypePaid, Field(discriminator="type")
]
