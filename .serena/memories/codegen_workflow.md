# Bot API Codegen Workflow

## How code generation works
aiogram uses `butcher` (via `aiogram-cli`) to auto-generate Python files from the Telegram Bot API schema.

### Source of truth
- `.butcher/schema/schema.json` — full parsed Bot API schema
- `.butcher/types/<TypeName>/entity.json` — parsed entity metadata (DO NOT edit)
- `.butcher/methods/<MethodName>/entity.json` — parsed method metadata (DO NOT edit)
- `.butcher/enums/<EnumName>/entity.json` — parsed enum metadata (DO NOT edit)
- `.butcher/templates/` — Jinja2 templates that produce Python code
- YAML alias/override files in `.butcher/types/`, `.butcher/methods/` — edit these for customizations

### Generated files (DO NOT hand-edit)
- `aiogram/types/*.py` (except `base.py`, `custom.py`, `_union.py` — framework internals)
- `aiogram/methods/*.py` (except `base.py`)
- `aiogram/enums/*.py`
- `aiogram/client/bot.py` (the `Bot` class shortcuts)
- `aiogram/types/__init__.py`, `aiogram/methods/__init__.py`

### Regeneration commands
```bash
uv run --extra cli butcher parse    # re-parse from API schema
uv run --extra cli butcher refresh  # refresh entity JSON from parsed schema
uv run --extra cli butcher apply all  # apply templates → generate Python files
```

### Adding a new type/method/shortcut
1. Update the `.butcher` YAML alias/config file for the entity
2. Run regeneration (parse → refresh → apply)
3. Run lint + mypy + tests
4. Commit both the `.butcher` config changes AND the generated Python files

### API version bumps (maintainers)
```bash
make update-api args=patch   # or minor/major
```
This runs butcher parse/refresh/apply + version bump scripts that update:
- `aiogram/__meta__.py`
- `README.rst`
- `docs/index.rst`

## Key constraint
The maintainers enforce: **never add types/methods/shortcuts by hand-editing generated files**. All changes must go through `.butcher` config so future regenerations preserve them.
