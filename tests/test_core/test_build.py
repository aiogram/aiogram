import os
import subprocess
import sys
import sysconfig
import tomllib
from pathlib import Path

import pytest

import aiogram
from aiogram import _core

ROOT = Path(__file__).parents[2]
FREE_THREADED = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))


def run_python(code: str) -> None:
    env = {key: value for key, value in os.environ.items() if key != "PYTHON_GIL"}
    subprocess.run([sys.executable, "-c", code], env=env, check=True)


def test_build_info():
    info = _core.build_info()
    assert set(info) == {"version", "pyo3_version", "profile", "lto", "target"}
    assert all(info.values())
    assert tuple(map(int, info["pyo3_version"].split(".")[:2])) >= (0, 30)
    assert info["profile"] in {"debug", "release"}
    if info["profile"] == "release":
        assert info["lto"] == "thin"


def test_versions_match():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == aiogram.__version__
    assert _core.__version__ == aiogram.__version__
    assert _core.build_info()["version"] == aiogram.__version__


def test_import_aiogram_does_not_load_core():
    run_python(
        "import sys, aiogram; "
        "assert 'aiogram._core' not in sys.modules; "
        "assert 'aiogram.utils._converters' not in sys.modules"
    )


def test_public_converters_module_does_not_load_core():
    # the declaration API (field, Key, Converter...) is stdlib-only (F-08 plan-10)
    run_python("import sys, aiogram.utils.converters; assert 'aiogram._core' not in sys.modules")


@pytest.mark.skipif(not FREE_THREADED, reason="needs a free-threaded build")
def test_gil_stays_disabled_without_python_gil_env():
    run_python("import sys, aiogram._core; assert not sys._is_gil_enabled()")
