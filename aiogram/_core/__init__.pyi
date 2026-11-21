# Hand-written stub of the native extension `aiogram._core` (crates/aiogram-core), checked
# against the built module by `make stubtest` (PD-36, as pydantic-core does).
#
# Stub-only package: the `.so` is the runtime module, and each native submodule (registered in
# `crates/aiogram-core/src/lib.rs`) has its own `<name>.pyi` beside this file. No `.py` here.
from typing import TypedDict, type_check_only

from . import conv as conv

__all__ = ["__version__", "build_info", "conv"]

__version__: str

@type_check_only
class BuildInfo(TypedDict):
    version: str
    pyo3_version: str
    profile: str
    lto: str
    target: str

def build_info() -> BuildInfo: ...
