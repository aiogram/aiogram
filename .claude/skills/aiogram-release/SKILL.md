---
name: aiogram-release
description: Cut an aiogram release — bump the version, build the changelog from the CHANGES fragments, verify the version-carrying files, tag. Use when asked to "prepare a release", "bump the version", "build the changelog", or "release 3.x.y".
---

# Prepare a release

Recurring maintainer chore — `aiogram/__meta__.py` and `CHANGES.rst` have each been
touched ~46 times in the last 300 commits, always in the same shape:
`Bump version` → `Bump changelog` → `Release X.Y.Z` + tag.

Maintainer-only, and it writes to the working tree. Confirm the target version with
the user before running anything, and never push or tag without being asked.

## 1. Preview the notes

```bash
rtk proxy make towncrier-draft            # rtk proxy uv run --extra docs towncrier build --draft
```

Every fragment in `CHANGES/` shows up here. Fix wording in the fragment files, not in
the draft. Categories: `feature`, `bugfix`, `doc`, `removal`, `misc`.

## 2. Bump

```bash
rtk proxy make bump args=patch            # or minor | major | to:3.31.0
```

Runs both scripts:

- `scripts/bump_version.py <part>` → `aiogram/__meta__.py::__version__`
- `scripts/bump_versions.py` → reads `.butcher/schema/schema.json` `api.version`, writes
  `.apiversion`, `__meta__.py::__api_version__`, the `API-<ver>-blue.svg` badge and the
  "Supports `Telegram Bot API …`" line in `README.rst`, and the badge in `docs/index.rst`

Verify all five landed:

```bash
rtk git diff --stat -- aiogram/__meta__.py .apiversion README.rst docs/index.rst
```

## 3. Build the changelog

```bash
rtk proxy make towncrier-build            # towncrier build --yes: consumes CHANGES/*.rst into CHANGES.rst
```

`rtk proxy make prepare-release` = step 2 + step 3 in one go. This is the only sanctioned way
`CHANGES.rst` gets edited.

## 4. Sanity

```bash
rtk proxy uv run python -c 'from aiogram import __version__, __api_version__; print(__version__, __api_version__)'
rtk git status --short               # CHANGES/ fragments must now be deleted, CHANGES.rst grown
rtk test uv run pytest tests -q
rtk proxy uv build
```

## 5. Tag (only on explicit request)

```bash
rtk proxy make release                     # git add . && commit "Release X.Y.Z" && git tag vX.Y.Z
```

Publishing runs from `.github/workflows/pypi-release.yml` on the tag — do not
`uv publish` by hand.

## Known wart

`scripts/bump_versions.py::get_package_version()` still reads
`pyproject.toml → tool.poetry.version`, which no longer exists since the move to
hatchling/uv. It is dead code (`main()` never calls it), so the bump works — but do not
reuse that function.
