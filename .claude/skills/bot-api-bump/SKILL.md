---
name: bot-api-bump
description: Drive a full Telegram Bot API version bump in aiogram from regeneration to green CI — codegen, missing imports, the hand-written enumeration sites, tests, docs, changelog and version files. Use when asked to "add support for Bot API X.Y", "update to the new Bot API", or after `make update-api`.
---

# Bot API version bump

The single largest recurring event in this repo — `Added full support for the Bot API X.Y`
lands roughly every release (9.1 → 10.2 in the visible history), each time touching
hundreds of files across `aiogram/types`, `aiogram/methods`, `aiogram/enums`,
`docs/api/**`, `.apiversion`, `README.rst` and `docs/index.rst`.

This skill is the checklist; each leg has its own skill — use them.

## 0. Inputs

Ask for the Bot API version, the aiogram issue/PR number, and the
`core.telegram.org/bots/api-changelog#<anchor>` URL. All three are needed later.

## 1. Regenerate

```bash
rtk proxy make update-api args=patch        # butcher parse → refresh → apply all → bump
```

`butcher` is a maintainer-only tool and is **not installed in this checkout**
(`rtk proxy uv run --extra cli butcher --help` → `Failed to spawn: butcher`). If it is missing,
the branch was probably produced elsewhere — start from step 2 against the existing
diff. Do not attempt to hand-generate a whole API version.

What `rtk proxy make bump` (`scripts/bump_versions.py`) rewrites, from
`.butcher/schema/schema.json` → `api.version`: `.apiversion`,
`aiogram/__meta__.py::__api_version__`, the API badge and support line in `README.rst`,
and the badge in `docs/index.rst`. `scripts/bump_version.py` bumps `__version__`
separately (`major|minor|patch|to:X.Y.Z`).

## 2. Scope the diff

```bash
rtk git diff --stat HEAD -- aiogram/ docs/
rtk git status --short -- aiogram/          # new files = new types/methods/enums
```

## 3. Fix what codegen missed — before writing any test

- **F821 undefined names** → skill `fix-codegen-imports`.
- **Hand-written enumeration sites** butcher never touches. A new `Update.<field>`
  needs `aiogram/types/update.py::event_type` and
  `aiogram/dispatcher/middlewares/user_context.py::resolve_event_context`; new message
  content needs `aiogram/enums/content_type.py` and `Message.content_type`. Details and
  the grep to find the rest: skill `test-bot-api-codegen`, step 2.
- **Enums scraped by regexp** from a doc sentence can silently contain another enum's
  members. Eyeball every new `aiogram/enums/*.py` against its source docstring.
- **`Default()` sentinels.** New `parse_mode`/`*_parse_mode` fields and the shortcuts
  that forward them must carry `Default("parse_mode")`, not `None` (#1873).
  `TestParseModeDefaultIsWired` catches this.
- **New `*Union` with a constant tag field** must render as a Pydantic discriminated
  union, or nested validation goes exponential (#1842).

## 4. Tests

Skill `test-bot-api-codegen` — it maps each kind of codegen change to the test file and
the pattern to mirror, and lists the guard tests whose failure *is* the to-do list.
Coverage target: 100%.

## 5. Changelog

Skill `aiogram-api-changelog` with the issue number and the changelog URL →
`CHANGES/<issue>.misc.rst`. Bot API bumps use the `misc` category.

## 6. Verify

```bash
rtk ruff format aiogram tests scripts examples
rtk ruff check --show-fixes --preview aiogram examples
rtk mypy aiogram
rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing
rtk proxy uv run --extra docs bash -c 'cd docs && make html'      # docs/api/** was regenerated
```

Then review with the `aiogram-pr-gate` agent. Release packaging (towncrier build,
version commit, tag) is the `aiogram-release` skill.
