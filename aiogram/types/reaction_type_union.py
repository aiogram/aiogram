from __future__ import annotations

from typing import Union

from .reaction_type_custom_emoji import ReactionTypeCustomEmoji
from .reaction_type_emoji import ReactionTypeEmoji
from .reaction_type_paid import ReactionTypePaid

ReactionTypeUnion = Union[ReactionTypeEmoji, ReactionTypeCustomEmoji, ReactionTypePaid]
