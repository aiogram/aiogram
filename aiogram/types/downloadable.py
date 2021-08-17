from typing import Protocol


class Downloadable(Protocol):
    file_id: str
