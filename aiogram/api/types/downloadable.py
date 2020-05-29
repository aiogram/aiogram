from typing_extensions import Protocol


class Downloadable(Protocol):
    file_id: str
