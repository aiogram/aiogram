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

`butcher` is not installed in this checkout (`uv run --extra cli butcher` → `Failed to spawn`), but it
can be built once, outside the repository (AGENTS.md, "Bot API/codegen workflow"):

```bash
git clone https://github.com/aiogram/butcher /tmp/butcher-src
uv venv /tmp/butcher-venv --python 3.11 && uv pip install --python /tmp/butcher-venv/bin/python /tmp/butcher-src
/tmp/butcher-venv/bin/python -m butcher.shell.main parse     # then refresh, apply all (repository root)
rtk proxy uv run python scripts/bump_versions.py             # `make bump` wants `args=` for bump_version.py
```

Do not hand-generate a whole API version. If the changelog entry is not published, stop.

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
  content needs `aiogram/enums/content_type.py` and `Message.content_type`. A new `Update`
  field also needs a `UserActor` trigger (`aiogram/test/actors.py`) and a `TRIGGERS` row
  (`tests/test_testing/test_triggers.py`); the every-variant-has-a-trigger guard fails otherwise. Details and
  the grep to find the rest: skill `test-bot-api-codegen`, step 2.
- **Migration data.** Deprecated fields land in `aiogram/_migration/data/*.json`: rerun
  `uv run python scripts/butcher_removal_inventory.py` and `scripts/butcher_signatures_3x.py`
  (no args), or `tests/test_migration_data` fails.
- **A method whose return type changed** (`getMe` → `BotFullInfo` in 10.5) breaks the tests that stub it
  with the old type (`tests/mocked_bot.py::bot_full_info`), the test toolkit's handler in
  `aiogram/test/modeling.py`, and `Bot.me()`, which keeps returning `User`.
- **Enums scraped by regexp** from a doc sentence can silently contain another enum's
  members. Eyeball every new `aiogram/enums/*.py` against its source docstring.
- **`Default()` sentinels.** New `parse_mode`/`*_parse_mode` fields and the shortcuts
  that forward them must carry `Default("parse_mode")`, not `None` (#1873).
  `TestParseModeDefaultIsWired` catches this.
- **New `*Union` with a constant tag field** must render as a Pydantic discriminated
  union, or nested validation goes exponential (#1842).

- **A changed return type or field is a design question, not a type error.** Before editing, find
  every hand-written consumer (`git grep` in `aiogram/`, `docs/`, `tests/`, the test toolkit), find
  the PR/issue that introduced each (`git log -S`, `gh pr view`), read what it promised (cache
  lifetime, failure behaviour, docs, tests) and ask the maintainer about each open choice before
  the first edit. `getMe` → `BotFullInfo` (10.5) is the example: `Bot.me()`, `Bot.usernames()`
  (#1984), `Dispatcher.start_polling`, `Command` and the toolkit all depended on its type.

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
