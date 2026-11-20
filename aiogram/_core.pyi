# Hand-written stub for the native extension (crates/aiogram-core).
from typing import TypedDict, type_check_only

__version__: str

@type_check_only
class BuildInfo(TypedDict):
    version: str
    pyo3_version: str
    profile: str
    lto: str
    target: str

def build_info() -> BuildInfo: ...
