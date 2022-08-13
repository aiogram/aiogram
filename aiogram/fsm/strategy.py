from enum import Enum, auto
from typing import Tuple


class FSMStrategy(Enum):
    USER_IN_CHAT = auto()
    CHAT = auto()
    GLOBAL_USER = auto()


def apply_strategy(chat_id: int, user_id: int, strategy: FSMStrategy) -> Tuple[int, int]:
    if strategy == FSMStrategy.CHAT:
        return chat_id, chat_id
    if strategy == FSMStrategy.GLOBAL_USER:
        return user_id, user_id
    return chat_id, user_id
