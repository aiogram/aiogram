import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]

# Built artifacts to check: `maturin build --release -o <dir>` and `maturin sdist -o <dir>`.
# Unset, the package is skipped; CI (core.yml, `Packaging`) sets it.
DIST_DIR = os.environ.get("AIOGRAM_DIST_DIR")

if DIST_DIR is None:
    collect_ignore_glob = ["test_*.py"]


def single(pattern: str) -> Path:
    assert DIST_DIR is not None
    found = sorted(Path(DIST_DIR).glob(pattern))
    assert len(found) == 1, f"expected one {pattern} in {DIST_DIR}, found {found}"
    return found[0]


@pytest.fixture(scope="session")
def tracked_package_files() -> set[str]:
    """Files of the ``aiogram`` package as git tracks them, relative to the repository root."""
    out = subprocess.run(
        ["git", "ls-files", "aiogram"], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return set(out.stdout.splitlines())
