import tarfile
import tomllib

import aiogram

from .conftest import single

sdist = single("*.tar.gz")
PREFIX = f"aiogram-{aiogram.__version__}/"


def members() -> set[str]:
    with tarfile.open(sdist) as archive:
        names = {member.name for member in archive.getmembers() if member.isfile()}
    assert all(name.startswith(PREFIX) for name in names)
    return {name.removeprefix(PREFIX) for name in names}


def test_top_level():
    # exact: a new top-level directory or file must be listed here, or excluded in pyproject.toml
    assert {name.split("/")[0] for name in members()} == {
        "Cargo.lock",
        "Cargo.toml",
        "LICENSE",
        "PKG-INFO",
        "README.rst",
        "aiogram",
        "crates",
        "pyproject.toml",
    }


def test_rust_sources():
    names = members()
    assert {
        "Cargo.lock",
        "crates/aiogram-core/Cargo.toml",
        "crates/aiogram-core/build.rs",
    } <= names
    assert "crates/aiogram-core/src/lib.rs" in names
    # the dev-only workspace crates (butcher, xtask) and build output stay out
    assert {name.split("/")[1] for name in names if name.startswith("crates/")} == {"aiogram-core"}
    assert not [name for name in names if "/target/" in f"/{name}"]
    # rustup would force the pinned CI toolchain (and a download) on every sdist build;
    # `rust-version` in Cargo.toml states the MSRV instead
    assert "rust-toolchain.toml" not in names


def test_workspace_members():
    with tarfile.open(sdist) as archive:
        file = archive.extractfile(f"{PREFIX}Cargo.toml")
        assert file is not None
        manifest = tomllib.loads(file.read().decode())
    assert manifest["workspace"]["members"] == ["crates/aiogram-core"]
    assert manifest["workspace"]["package"]["rust-version"]


def test_package_files(tracked_package_files: set[str]):
    package = {name for name in members() if name.startswith("aiogram/")}
    assert package == tracked_package_files
