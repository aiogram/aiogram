# AGENTS.md

This file defines how coding agents should contribute to `aiogram` on `dev-3.x`.

## Scope and defaults

- Base branch: `dev-3.x`
- Python: `>=3.10`
- Main tooling: `uv`, `ruff`, `mypy`, `pytest`, `towncrier`, `butcher`
- Keep diffs focused; avoid unrelated refactors/reformatting.

## Setup

```bash
uv sync --all-extras --group dev --group test
uv run pre-commit install
```

Note: `uv run pre-commit install` writes hooks to the shared repository `.git/hooks`
(common for all worktrees), not only for the current worktree.

## Mandatory local checks before PR

Code style/lint in this repository is enforced via Ruff (`ruff check` + `ruff format`).

Quick loop (recommended for most PR iterations):

```bash
uv run ruff check --show-fixes --preview aiogram examples
uv run ruff format --check --diff aiogram tests scripts examples
uv run mypy aiogram
uv run pytest tests
```

Full loop (run before final review request):

```bash
# Run quick loop first, then:
uv run pytest --redis redis://<host>:<port>/<db> tests  # when Redis storage paths are affected
uv run pytest --mongo mongodb://<user>:<password>@<host>:<port> tests  # when Mongo storage paths are affected
uv run --extra docs bash -c 'cd docs && make html'  # when docs or generated API docs are affected
```

If changes touch Redis/Mongo storage behavior, run integration variants too:

```bash
uv run pytest --redis redis://<host>:<port>/<db> tests
uv run pytest --mongo mongodb://<user>:<password>@<host>:<port> tests
```

Run these only if you have accessible Redis/Mongo instances in your environment.


## Changelog rules (CI-gated)

- Add `CHANGES/<issue-or-pr>.<category>.rst` unless PR has `skip news` label.
- Valid categories: `feature`, `bugfix`, `doc`, `removal`, `misc`.
- Changelog text must describe user-visible behavior changes, not process/org details.
- Do not edit `CHANGES.rst` directly for regular PRs.

## Bot API/codegen workflow (critical)

`aiogram` API layers are generated. For Bot API related work:

- Prefer editing generator inputs (`.butcher/**/*.yml`, aliases, templates) instead of hand-editing generated code.
- Do not manually edit `.butcher/**/entity.json` (parser/codegen will overwrite it).
- For new shortcuts, add alias/config in `.butcher` and regenerate.
- Regeneration flow:

```bash
uv run --extra cli butcher parse
uv run --extra cli butcher refresh
uv run --extra cli butcher apply all
```

For maintainers preparing an API/version bump only:

```bash
make update-api args=patch
```

`make update-api args=...` also runs version bump scripts and updates version-related files
(`aiogram/__meta__.py`, `README.rst`, `docs/index.rst`).

After regeneration, run lint/type/tests again.

## Maintainer review signals (recent PRs)

These patterns repeatedly appeared in maintainer feedback and should be treated as hard constraints:

- Keep generation path consistent: shortcuts/features should be added through `.butcher` config + generation, not ad-hoc manual edits.
- Keep test style consistent with existing suite; avoid introducing new dependencies for small tests.
- Preserve framework contracts (e.g., dispatcher/workflow data passed to startup/shutdown callbacks).
- When fixing generated API metadata/docs, update the source mapping in `.butcher` so future regenerations keep the fix.

## Documentation work

For docs changes:

```bash
uv run --extra docs sphinx-autobuild --watch aiogram/ --watch CHANGES.rst --watch README.rst docs/ docs/_build/
```

`sphinx-autobuild` is long-running by design.

Or quick build:

```bash
uv run --extra docs bash -c 'cd docs && make html'
```

## PR quality checklist

Before requesting review:

1. Tests added/updated for behavior changes.
2. Local lint/type/tests pass.
3. Changelog fragment added (or `skip news` is justified).
4. If codegen-related: generated files and source config are both updated coherently.
5. PR body includes clear reproduction/validation steps.
