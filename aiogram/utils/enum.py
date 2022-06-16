import enum


class AutoName(enum.Enum):

    def _generate_next_value_(self, start, count, last_values) -> str:
        return self.lower()
