import enum


class AutoName(str, enum.Enum):

    def _generate_next_value_(self, start, count, last_values) -> str:
        return self.lower()
