# Code Style & Conventions

## General
- `from __future__ import annotations` at the top of every Python file
- Full type hints on all function signatures and class fields
- Max line length: **99** characters (ruff enforced)
- snake_case for Python names; camelCase used only in `__api_method__` strings

## Pydantic models
- All Telegram types extend `TelegramObject(BotContextController, BaseModel)` from `aiogram/types/base.py`
- `TelegramObject` is frozen; use `MutableTelegramObject` when mutation is needed
- Fields default to `None` for optional API parameters; use `Field(None, json_schema_extra={"deprecated": True})` for deprecated fields
- Use `Default("key")` sentinel (from `aiogram.client.default`) for user-configurable defaults like `parse_mode`, `protect_content`
- `TYPE_CHECKING` guards for circular imports — keep runtime imports lean

## API Methods
- Each method is a class inheriting `TelegramMethod[ReturnType]` from `aiogram/methods/base.py`
- Required class attrs: `__returning__` (return type), `__api_method__` (camelCase string)
- Fields with `None` default = optional param
- Method docstring format: short description + `Source: https://core.telegram.org/bots/api#methodname`
- File name: snake_case of method name (e.g., `SendMessage` → `send_message.py`)

## Imports order (ruff/isort enforced)
1. stdlib
2. third-party
3. `aiogram` (first-party)
4. relative imports

## Ruff rules enforced
- A (annotations), B (bugbear), C4 (comprehensions), DTZ (datetimez), E, F, I (isort), PERF, PL (pylint), Q (quotes), RET, SIM, T10, T20, UP (pyupgrade)
- Several PLR rules disabled (Telegram API naturally has many params/methods)
- `F401` disabled (re-exports in `__init__.py` intentional)

## Code generation convention
- **Never hand-edit generated files** (`.butcher/**/entity.json`, auto-generated `aiogram/types/*.py`, `aiogram/methods/*.py`, `aiogram/enums/*.py`)
- Add features via `.butcher` YAML config/aliases + templates, then regenerate
- After codegen: always run lint + mypy

## Naming patterns
- Enums: PascalCase class, UPPER_SNAKE members (e.g., `ContentType.TEXT`)
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>` with `async def test_<scenario>(self, bot: MockedBot)`
