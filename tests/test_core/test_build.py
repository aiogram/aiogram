import ast
import importlib.metadata
import importlib.util
import os
import subprocess
import sys
import sysconfig
import tomllib
import types
from importlib.machinery import EXTENSION_SUFFIXES
from pathlib import Path

import pytest

import aiogram
from aiogram import _core

ROOT = Path(__file__).parents[2]
FREE_THREADED = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
# the native submodules: one stub each beside aiogram/_core/__init__.pyi (AGENTS.md)
SUBMODULES = sorted(
    p.stem for p in (ROOT / "aiogram" / "_core").glob("*.pyi") if p.stem != "__init__"
)


def run_python(code: str) -> None:
    env = {key: value for key, value in os.environ.items() if key != "PYTHON_GIL"}
    subprocess.run([sys.executable, "-c", code], env=env, check=True)


def test_core_is_the_extension():
    # without a built .so the stub-only aiogram/_core/ directory imports as an empty namespace
    assert _core.__file__ is not None, "aiogram._core is not built for this interpreter"
    assert _core.__file__.endswith(tuple(EXTENSION_SUFFIXES))


def test_build_info():
    info = _core.build_info()
    assert set(info) == {"version", "pyo3_version", "profile", "lto", "target"}
    assert all(info.values())
    assert tuple(map(int, info["pyo3_version"].split(".")[:2])) >= (0, 30)
    assert info["profile"] in {"debug", "release"}
    if info["profile"] == "release":
        assert info["lto"] == "thin"


def load_bump_version() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("bump_version", ROOT / "scripts/bump_version.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bump_version = load_bump_version()


def test_versions_match():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    cargo = tomllib.loads((ROOT / "crates/aiogram-core/Cargo.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == aiogram.__version__
    assert cargo["package"]["version"] == bump_version.cargo_version(aiogram.__version__)
    assert importlib.metadata.version("aiogram") == aiogram.__version__
    assert _core.__version__ == aiogram.__version__
    assert _core.build_info()["version"] == aiogram.__version__


def test_development_status_matches_version():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    statuses = [
        c for c in pyproject["project"]["classifiers"] if c.startswith("Development Status")
    ]
    assert statuses == [bump_version.development_status(aiogram.__version__)]


@pytest.mark.parametrize(
    ("version", "cargo", "status"),
    [
        ("4.0.0", "4.0.0", "5 - Production/Stable"),
        ("4.0.0a1", "4.0.0-alpha.1", "3 - Alpha"),
        ("4.0.0b2", "4.0.0-beta.2", "4 - Beta"),
        ("4.0.0rc1", "4.0.0-rc.1", "4 - Beta"),
    ],
)
def test_bump_version_forms(version: str, cargo: str, status: str):
    assert bump_version.cargo_version(version) == cargo
    assert bump_version.development_status(version) == f"Development Status :: {status}"


@pytest.mark.parametrize("version", ["4.0.0.dev1", "4.0.0.post1", "4.0.0+local", "4.0.0-alpha1"])
def test_bump_version_rejects(version: str):
    with pytest.raises(ValueError, match="use X.Y.Z"):
        bump_version.parse(version)


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


def stub_names(name: str) -> list[str]:
    """``__all__`` of the stub of ``aiogram._core.<name>``."""
    tree = ast.parse((ROOT / "aiogram" / "_core" / f"{name}.pyi").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name}.pyi has no __all__")


def test_submodules_match_stubs():
    registered = sorted(
        name for name, value in vars(_core).items() if isinstance(value, types.ModuleType)
    )
    assert registered == SUBMODULES
    assert SUBMODULES  # the glob found the stubs


@pytest.mark.parametrize("name", SUBMODULES)
def test_submodule_imports_in_fresh_process(name: str):
    names = stub_names(name)
    module = f"aiogram._core.{name}"
    run_python(
        f"import sys; from {module} import {', '.join(names)}; "
        f"m = sys.modules[{module!r}]; assert m.__name__ == {module!r}; "
        f"import importlib.util; assert importlib.util.find_spec({module!r}).name == {module!r}; "
        f"assert all(getattr(m, n).__module__ == {module!r} for n in {names!r}); "
        f"assert not {FREE_THREADED} or not sys._is_gil_enabled()"
    )
