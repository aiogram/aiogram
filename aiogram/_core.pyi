# Hand-written stub for the native extension (crates/aiogram-core).
from collections.abc import Sequence
from typing import Any, TypedDict, type_check_only

__version__: str

@type_check_only
class BuildInfo(TypedDict):
    version: str
    pyo3_version: str
    profile: str
    lto: str
    target: str

def build_info() -> BuildInfo: ...

class ModelSchema:
    """Rust backend of ``aiogram.utils._converters.ModelConverter`` (F-08, PD-35)."""

    def __init__(self, converter: Any, /) -> None: ...
    def load_dict(self, value: Any, /) -> Any: ...
    def load_json(self, data: bytes | str, /) -> Any: ...
    def from_flat(self, parts: Sequence[str], /) -> Any: ...
    def to_flat(self, value: Any, /) -> list[str]: ...
