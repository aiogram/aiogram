# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6"]
# ///
"""Reject ``uses:`` references that are not version tags or commit SHAs.

zizmor's ``ref-pin`` policy only checks that a ref is present, not what it points at,
so ``owner/action@main`` passes it. A regex cannot tell a ``v7`` tag from a ``v7``
branch either; what this script can do is reject refs that do not even look like a
version tag (``v?1.2.3``) or a 40-hex SHA: ``main``, ``master``, ``release/x``,
``2.x``, ``v4-beta``. The YAML is parsed, not grepped, so quoted keys and values, flow
mappings, composite actions and reusable-workflow jobs are all covered.

Run with ``uv run scripts/check_action_refs.py`` (dependencies come from the inline
metadata above, the project environment is not used).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIR = ROOT / ".github"
PINNED = re.compile(r"^(v?[0-9]+(\.[0-9]+)*|[0-9a-f]{40})$")
# the ref PyPA recommends for its publisher; the one documented exception
EXCEPTIONS = (re.compile(r"^pypa/gh-action-pypi-publish@release/v[0-9]+$"),)


def iter_uses(node: object):
    """Yield every string value stored under a ``uses`` key, at any depth."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "uses" and isinstance(value, str):
                yield value
            else:
                yield from iter_uses(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_uses(item)


def is_pinned(uses: str) -> bool:
    if "@" not in uses or uses.startswith(("./", "docker://")):
        return True  # local action or container image: nothing to pin
    if any(pattern.match(uses) for pattern in EXCEPTIONS):
        return True
    return bool(PINNED.match(uses.rsplit("@", 1)[1]))


def main() -> int:
    failures: list[str] = []
    for path in sorted(p for p in SCAN_DIR.rglob("*") if p.suffix in {".yml", ".yaml"}):
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            failures.append(f"{path.relative_to(ROOT)}: cannot parse YAML: {exc}")
            continue
        failures.extend(
            f"{path.relative_to(ROOT)}: uses: {uses}"
            for uses in iter_uses(document)
            if not is_pinned(uses)
        )
    if failures:
        sys.stdout.write("\n".join(failures) + "\n")
        sys.stdout.write(
            "::error::action refs above are not pinned to a version tag or commit SHA\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
