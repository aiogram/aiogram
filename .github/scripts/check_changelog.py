"""Check that a pull request adds a towncrier newsfragment.

Reads the list of files changed by the pull request (one path per line) and applies the
same rules as ``towncrier check``, without needing the pull request code to be checked
out: the towncrier configuration is read from the base repository, and the file list is
provided by the caller (``gh api .../pulls/<number>/files``).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import tomllib


def main(changed_files_path: str) -> int:
    config = tomllib.loads(Path("pyproject.toml").read_text())["tool"]["towncrier"]
    directory = config.get("directory", "newsfragments").strip("/")
    news_file = config.get("filename", "NEWS.rst")
    categories = [
        fragment_type["directory"]
        for fragment_type in config.get("type", [])
        if fragment_type.get("check", True)
    ]

    changed_files = [
        line.strip() for line in Path(changed_files_path).read_text().splitlines() if line.strip()
    ]

    print("Looking at these files:")
    print("----")
    for number, name in enumerate(changed_files, start=1):
        print(f"{number}. {name}")
    print("----")

    if not changed_files:
        print("No changed files, so no newsfragment required.")
        return 0

    if news_file in changed_files:
        print(f"Checks SKIPPED: {news_file} changes detected.")
        return 0

    any_category = "|".join(re.escape(category) for category in categories)
    fragment_pattern = re.compile(
        rf"^{re.escape(directory)}/[^/]+\.(?:{any_category})(?:\.[^/]+)?$"
    )
    fragments = [name for name in changed_files if fragment_pattern.match(name)]

    if fragments:
        print("Found:")
        for number, name in enumerate(fragments, start=1):
            print(f"{number}. {name}")
        return 0

    print(
        f"No new newsfragments found in {directory}/. "
        f"Expected a file named <issue or PR number>.<category>.rst, "
        f"where category is one of: {', '.join(categories)}."
    )
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <changed-files-list>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
