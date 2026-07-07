# Project Overview: aiogram

## Purpose
**aiogram** is a modern, fully asynchronous Python framework for the Telegram Bot API (currently supports Bot API 9.5+). It provides a high-level interface for building Telegram bots using asyncio.

## Tech Stack
- **Python**: 3.10–3.14 (also supports PyPy)
- **Async runtime**: asyncio + aiohttp (HTTP client)
- **Data validation**: Pydantic v2
- **Package manager**: `uv`
- **Linter/formatter**: `ruff` (check + format)
- **Type checker**: `mypy`
- **Testing**: `pytest` with `pytest-asyncio`, `aresponses`
- **Docs**: Sphinx (reStructuredText), `sphinx-autobuild`
- **Changelog**: `towncrier`
- **Code generation**: `butcher` (aiogram-cli) — generates types, methods, enums from Bot API schema

## Key Links
- Docs (English): https://docs.aiogram.dev/en/dev-3.x/
- GitHub: https://github.com/aiogram/aiogram/
- Bot API schema: `.butcher/schema/schema.json`

## Architecture Summary
The framework is layered:
1. **`aiogram/client/`** — `Bot` class (all API methods as shortcuts), session management, context controller
2. **`aiogram/types/`** — Pydantic models for all Telegram types (`TelegramObject` base)
3. **`aiogram/methods/`** — `TelegramMethod[ReturnType]` subclasses, one per Bot API method
4. **`aiogram/dispatcher/`** — Dispatcher, Router (blueprints), middleware, event observers
5. **`aiogram/filters/`** — Filter classes for routing
6. **`aiogram/fsm/`** — Finite State Machine (states, storage backends)
7. **`aiogram/enums/`** — Enumerations (ContentType, UpdateType, etc.)
8. **`aiogram/utils/`** — Text decoration, keyboards, i18n, etc.
9. **`aiogram/webhook/`** — Webhook server integrations (aiohttp, FastAPI, etc.)
10. **`.butcher/`** — Code generation inputs: YAML/JSON configs for types/methods/enums + Jinja2 templates

## Optional extras
- `fast` — uvloop + aiodns
- `redis` — Redis FSM storage
- `mongo` — MongoDB FSM storage
- `proxy` — SOCKS proxy support
- `i18n` — Babel-based i18n
- `cli` — `butcher` codegen CLI
- `signature` — cryptographic signature verification
