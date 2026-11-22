#!/usr/bin/env python3
"""Version bumping script for aiogram (replaces hatch version).

``aiogram/__meta__.py`` is the source of truth. This script also writes the static copies:
``pyproject.toml`` (PEP 440, read by maturin) with its ``Development Status`` classifier, and
``crates/aiogram-core/Cargo.toml`` (semver, the ``aiogram._core.__version__`` that build.rs turns
back into PEP 440). tests/test_core/test_build.py checks they all match.
"""

import re
import sys
from pathlib import Path

from packaging.version import Version

META = Path("aiogram/__meta__.py")
PYPROJECT = Path("pyproject.toml")
CARGO = Path("crates/aiogram-core/Cargo.toml")

META_VERSION = re.compile(r'^__version__ = "(.+)"$', flags=re.M)
COPY_VERSION = re.compile(r'^version = ".+"$', flags=re.M)
DEVELOPMENT_STATUS = re.compile(r'"Development Status :: [^"]+"')

# PEP 440 pre-release letter -> semver pre-release tag (build.rs maps it back)
SEMVER_PRE = {"a": "alpha", "b": "beta", "rc": "rc"}
# alpha and beta are not GA (D121); Production/Stable from the final release on
STATUS = {"a": "3 - Alpha", "b": "4 - Beta", "rc": "4 - Beta", None: "5 - Production/Stable"}


def parse(version: str) -> Version:
    parsed = Version(version)
    if (
        str(parsed) != version
        or parsed.epoch
        or parsed.dev is not None
        or parsed.post is not None
        or parsed.local
    ):
        raise ValueError(f"{version!r}: use X.Y.Z, X.Y.ZaN, X.Y.ZbN or X.Y.ZrcN")
    return parsed


def cargo_version(version: str) -> str:
    """Semver form of a PEP 440 version: ``4.0.0a1`` -> ``4.0.0-alpha.1``."""
    parsed = parse(version)
    if parsed.pre is None:
        return parsed.base_version
    stage, number = parsed.pre
    return f"{parsed.base_version}-{SEMVER_PRE[stage]}.{number}"


def development_status(version: str) -> str:
    pre = parse(version).pre
    return f"Development Status :: {STATUS[pre[0] if pre else None]}"


def substitute(path: Path, pattern: re.Pattern[str], line: str) -> None:
    content, count = pattern.subn(line, path.read_text(), count=1)
    if not count:
        raise ValueError(f"Could not find {pattern.pattern} in {path}")
    path.write_text(content)


def write_version(version: str) -> None:
    parse(version)
    substitute(META, META_VERSION, f'__version__ = "{version}"')
    substitute(PYPROJECT, COPY_VERSION, f'version = "{version}"')
    substitute(PYPROJECT, DEVELOPMENT_STATUS, f'"{development_status(version)}"')
    substitute(CARGO, COPY_VERSION, f'version = "{cargo_version(version)}"')


def bump_version(part: str) -> str:
    match = META_VERSION.search(META.read_text())
    if not match:
        raise ValueError(f"Could not find version in {META}")
    current = parse(match.group(1))
    major, minor, patch = current.release

    if current.pre is not None and not part.startswith("to:"):
        # 4.0.0rc1 + patch would skip 4.0.0 itself
        raise ValueError(f"{current} is a pre-release: name the next version with to:X.Y.Z")
    if part == "major":
        new_version = f"{major + 1}.0.0"
    elif part == "minor":
        new_version = f"{major}.{minor + 1}.0"
    elif part == "patch":
        new_version = f"{major}.{minor}.{patch + 1}"
    elif part.startswith("to:"):
        new_version = part.removeprefix("to:")
    else:
        raise ValueError(f"Unknown part: {part}. Use major, minor, patch, or to:X.Y.Z[aN|bN|rcN]")

    write_version(new_version)
    return new_version


if __name__ == "__main__":
    if len(sys.argv) != 2:  # noqa: PLR2004
        print("Usage: python scripts/bump_version.py [major|minor|patch|to:X.Y.Z[aN|bN|rcN]]")  # noqa: T201
        sys.exit(1)

    new_version = bump_version(sys.argv[1])
    print(f"Bumped version to {new_version}")  # noqa: T201
