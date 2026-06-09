# Codebase Structure

## Top-level layout
```
aiogram/           # Main package
.butcher/          # Code generation inputs (DO NOT edit entity.json files)
tests/             # Test suite
docs/              # Sphinx documentation (RST)
examples/          # Example bot scripts
scripts/           # Version bump scripts
CHANGES/           # Towncrier changelog fragments (CHANGES/<issue>.<category>.rst)
```

## aiogram/ package
```
aiogram/
├── __init__.py         # Public API re-exports
├── __meta__.py         # Version (hatch reads this)
├── exceptions.py       # Framework exceptions
├── loggers.py          # Named loggers
├── client/
│   ├── bot.py          # Bot class — all API methods as async shortcuts
│   ├── session/        # HTTP session backends (aiohttp, base)
│   ├── default.py      # Default() sentinel for configurable defaults
│   └── context_controller.py  # Bot context injection into models
├── types/
│   ├── base.py         # TelegramObject (Pydantic BaseModel), MutableTelegramObject
│   ├── *.py            # One file per Telegram type
│   └── __init__.py     # Exports all types
├── methods/
│   ├── base.py         # TelegramMethod[T] base class
│   ├── *.py            # One file per API method (e.g., send_message.py → SendMessage)
│   └── __init__.py
├── enums/
│   ├── content_type.py # ContentType enum
│   ├── update_type.py  # UpdateType enum
│   └── *.py
├── dispatcher/
│   ├── dispatcher.py   # Dispatcher (main update processor)
│   ├── router.py       # Router (Blueprint-style routing)
│   ├── middlewares/    # Middleware system
│   ├── event/          # Event observer, typed decorators
│   └── flags/          # Handler flags
├── filters/            # Built-in filters (Command, StateFilter, etc.)
├── fsm/
│   ├── context.py      # FSMContext
│   ├── state.py        # State, StatesGroup
│   └── storage/        # Memory, Redis, MongoDB storage backends
├── handlers/           # Base handler types
├── utils/
│   ├── keyboard.py     # Keyboard builder utilities
│   ├── text_decorations.py  # HTML/Markdown formatting
│   └── i18n/           # Internationalization support
└── webhook/            # Webhook integrations (aiohttp, SimpleRequestHandler, etc.)
```

## .butcher/ (Code generation)
```
.butcher/
├── schema/schema.json  # Full Bot API schema (source of truth)
├── types/              # Per-type entity.json + optional alias YAML overrides
├── methods/            # Per-method entity.json + optional alias YAML overrides
├── enums/              # Per-enum entity.json + optional YAML overrides
└── templates/          # Jinja2 templates for generated Python files
```

**Rule**: Edit `.yml` alias files or templates in `.butcher/`, never `.entity.json` files directly. Regenerate after changes.

## tests/ layout
```
tests/
├── conftest.py         # Shared fixtures (bot, dispatcher, etc.)
├── mocked_bot.py       # MockedBot for testing without real HTTP
├── test_api/
│   ├── test_types/     # Tests for Telegram types
│   ├── test_methods/   # Tests for API method classes
│   └── test_client/    # HTTP client tests
├── test_dispatcher/    # Dispatcher/Router/Middleware tests
├── test_filters/       # Filter tests
├── test_fsm/           # FSM and storage tests
├── test_handler/       # Handler tests
├── test_utils/         # Utility tests
└── test_webhook/       # Webhook integration tests
```
