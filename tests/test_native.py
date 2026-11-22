import sys
from importlib.machinery import EXTENSION_SUFFIXES, ModuleSpec

import pytest

from aiogram import _native


def test_core_found():
    _native.require_core()


@pytest.mark.parametrize("spec", [None, ModuleSpec("aiogram._core", None, is_package=True)])
def test_core_missing(monkeypatch: pytest.MonkeyPatch, spec: ModuleSpec | None):
    monkeypatch.setattr(_native, "find_spec", lambda name: spec)
    with pytest.raises(ImportError) as exc_info:
        _native.require_core()
    message = str(exc_info.value)
    assert f"cp{sys.version_info.major}{sys.version_info.minor}" in message
    assert f"_core{EXTENSION_SUFFIXES[0]}" in message
    assert _native.INSTALL_DOCS_URL in message
    assert exc_info.value.name == "aiogram._core"
