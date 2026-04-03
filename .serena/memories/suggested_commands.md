# Suggested Commands

## Setup
```bash
uv sync --all-extras --group dev --group test
uv run pre-commit install
```

## Lint & Format (quick loop — use before every commit)
```bash
uv run ruff check --show-fixes --preview aiogram examples
uv run ruff format --check --diff aiogram tests scripts examples
uv run mypy aiogram
```

## Auto-fix formatting
```bash
uv run ruff format aiogram tests scripts examples
uv run ruff check --fix aiogram tests scripts examples
```

## Run tests
```bash
uv run pytest tests                                                   # basic
uv run pytest tests --redis redis://localhost:6379/0                  # with Redis
uv run pytest tests --mongo mongodb://mongo:mongo@localhost:27017     # with MongoDB
```

## Build docs
```bash
# Live-reload dev server
uv run --extra docs sphinx-autobuild --watch aiogram/ --watch CHANGES.rst --watch README.rst docs/ docs/_build/
# One-shot build
uv run --extra docs bash -c 'cd docs && make html'
```

## Code generation (Bot API codegen)
```bash
# After editing .butcher/*.yml or templates:
uv run --extra cli butcher parse
uv run --extra cli butcher refresh
uv run --extra cli butcher apply all
```

## API version bump (maintainers only)
```bash
make update-api args=patch   # runs butcher parse/refresh/apply + version bump
```

## Changelog
```bash
# Preview draft
uv run --extra docs towncrier build --draft
# Build final
uv run --extra docs towncrier build --yes
```

## Clean build artifacts
```bash
make clean
```

## Build package
```bash
uv build
```
