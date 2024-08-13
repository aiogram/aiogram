from enum import Enum, auto
from typing import Optional, Tuple


class FSMStrategy(Enum):
    """
    FSM strategy for storage key generation.
    """

    USER_IN_CHAT = auto()
    """State will be stored for each user in chat."""
    CHAT = auto()
    """State will be stored for each chat globally without separating by users."""
    GLOBAL_USER = auto()
    """State will be stored globally for each user globally."""
    USER_IN_TOPIC = auto()
    """State will be stored for each user in chat and topic."""
    CHAT_TOPIC = auto()
    """State will be stored for each chat and topic, but not separated by users."""


def apply_strategy(
    strategy: FSMStrategy,
    chat_id: int,
    user_id: int,
    thread_id: Optional[int] = None,
) -> Tuple[int, int, Optional[int]]:
    if strategy == FSMStrategy.CHAT:
        return chat_id, chat_id, None
    if strategy == FSMStrategy.GLOBAL_USER:
        return user_id, user_id, None
    if strategy == FSMStrategy.USER_IN_TOPIC:
        return chat_id, user_id, thread_id
    if strategy == FSMStrategy.CHAT_TOPIC:
        return chat_id, chat_id, thread_id

    return chat_id, user_id, None
