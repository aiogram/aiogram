# Hand-written stub for the native extension (crates/aiogram-core), checked against the
# built module by `make stubtest` (PD-35, as pydantic-core does).
from collections.abc import Sequence
from typing import Any, TypedDict, final, type_check_only

from typing_extensions import Self

__all__ = ["__version__", "ModelSchema", "build_info"]

__version__: str

@type_check_only
class BuildInfo(TypedDict):
    version: str
    pyo3_version: str
    profile: str
    lto: str
    target: str

def build_info() -> BuildInfo: ...
@final
class ModelSchema:
    """Rust backend of ``aiogram.utils._converters.ModelConverter`` (F-08, PD-35)."""

    def __new__(cls, converter: Any) -> Self: ...
    def load_dict(self, value: Any) -> Any: ...
    def load_json(self, data: bytes | str) -> Any: ...
    def from_flat(self, parts: Sequence[str]) -> Any: ...
    def to_flat(self, value: Any) -> list[str]: ...
