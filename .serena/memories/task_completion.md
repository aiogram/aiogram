# Task Completion Checklist

Run these before marking any task done or requesting review.

## Quick loop (every PR)
```bash
uv run ruff check --show-fixes --preview aiogram examples
uv run ruff format --check --diff aiogram tests scripts examples
uv run mypy aiogram
uv run pytest tests
```

## Codegen tasks (when touching .butcher/ or generated API files)
```bash
uv run --extra cli butcher parse
uv run --extra cli butcher refresh
uv run --extra cli butcher apply all
# Then re-run quick loop
```

## Integration tests (only if Redis/Mongo storage touched)
```bash
uv run pytest --redis redis://localhost:6379/0 tests
uv run pytest --mongo mongodb://mongo:mongo@localhost:27017 tests
```

## Docs (only if docs/ or public API changed)
```bash
uv run --extra docs bash -c 'cd docs && make html'
```

## Changelog fragment (required unless PR has `skip news` label)
- Create `CHANGES/<issue-or-pr-number>.<category>.rst`
- Valid categories: `feature`, `bugfix`, `doc`, `removal`, `misc`
- Content: user-visible behavior description (not internal/process details)
- Do NOT edit `CHANGES.rst` directly

## PR quality checklist
1. Tests added/updated for all behavior changes
2. Quick loop passes (ruff + mypy + pytest)
3. Changelog fragment added (or justified `skip news`)
4. If codegen-related: both `.butcher` source config AND generated files updated
5. PR body has clear reproduction/validation steps
