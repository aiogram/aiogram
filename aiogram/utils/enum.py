import enum
from typing import Any, List


class AutoName(str, enum.Enum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: List[Any]) -> str:
        return name.lower()
