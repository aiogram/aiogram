try:
    from typing import Protocol
except ImportError:  # pragma: no cover
    from typing_extensions import Protocol  # type: ignore


class Downloadable(Protocol):
    file_id: str
