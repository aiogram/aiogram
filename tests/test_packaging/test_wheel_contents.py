import os
import subprocess
import sys
import zipfile
from importlib.machinery import EXTENSION_SUFFIXES
from pathlib import Path

import pytest

import aiogram
from aiogram._native import INSTALL_DOCS_URL

from .conftest import single

wheel = single("*.whl")


@pytest.fixture(scope="module")
def names() -> list[str]:
    with zipfile.ZipFile(wheel) as archive:
        return archive.namelist()


@pytest.fixture
def unpacked(tmp_path: Path) -> Path:
    # a wheel is a zip of its install layout: unpacked, it is an installed copy on its own path
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(tmp_path)
    return tmp_path


def run_installed(path: Path, code: str) -> subprocess.CompletedProcess[str]:
    # -P plus PYTHONPATH: the unpacked wheel, not the checkout, provides `aiogram`; its
    # dependencies come from the current environment
    env = {**os.environ, "PYTHONPATH": str(path)}
    return subprocess.run(
        [sys.executable, "-P", "-c", code], env=env, capture_output=True, text=True, check=False
    )


def test_top_level(names: list[str]):
    assert {name.split("/")[0] for name in names} == {
        "aiogram",
        f"aiogram-{aiogram.__version__}.dist-info",
    }


def test_package_files(names: list[str], tracked_package_files: set[str]):
    package = {name for name in names if name.startswith("aiogram/")}
    core = [name for name in package if name.startswith("aiogram/_core.")]
    assert len(core) == 1, core
    assert core[0].endswith(tuple(EXTENSION_SUFFIXES))
    # every tracked file (sources, stubs, py.typed, registry.toml) and nothing else
    assert package - set(core) == tracked_package_files
    assert {
        "aiogram/py.typed",
        "aiogram/_core/__init__.pyi",
        "aiogram/_migration/registry.toml",
    } <= package


def test_installed_wheel_imports(unpacked: Path):
    result = run_installed(
        unpacked,
        "import importlib.metadata, aiogram, aiogram._core as core; "
        "print(aiogram.__file__, core.__file__, aiogram.__version__, core.__version__, "
        "importlib.metadata.version('aiogram'))",
    )
    assert result.returncode == 0, result.stderr
    package_file, core_file, *versions = result.stdout.split()
    assert Path(package_file).is_relative_to(unpacked)
    assert Path(core_file).is_relative_to(unpacked)
    assert versions == [aiogram.__version__] * 3


def test_installed_wheel_without_core(unpacked: Path):
    for core in (unpacked / "aiogram").glob("_core.*"):
        core.unlink()
    result = run_installed(unpacked, "import aiogram")
    assert result.returncode == 1
    error = result.stderr.strip().splitlines()[-1]
    assert error.startswith("ImportError: aiogram's compiled core is missing")
    assert f"cp{sys.version_info.major}{sys.version_info.minor}" in error
    assert INSTALL_DOCS_URL in error
