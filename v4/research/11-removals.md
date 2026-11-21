# 11 — Legacy removals in 4.0

An audit of `dev-3.x` for code that exists only for backward compatibility (with 2.x, older 3.x APIs or older Bot
API versions), or that is meaningless once types stop being pydantic models. Every item here goes into the
3→4 migration guide.

## Decisions

| # | Decision |
|---|---|
| **D12** | `event_from_user`, `event_chat`, `event_thread_id` are **no longer injected**. Only `event_context` remains (`.user`, `.chat`, `.thread_id`, `.business_connection_id`). |
| **D13** | `aiogram.utils.markdown` is **removed**. Use `aiogram.utils.formatting` (`Bold(...)`, `Text(...).as_kwargs()`) or `html.bold(html.quote(x))`. |
| **D14** | `CallbackData` is **no longer pydantic**: it becomes a dataclass-style class with the same declaration syntax. **pydantic is dropped from aiogram's dependencies**: it is neither required nor an optional extra. |
| **D42** | **Class-based handlers (`aiogram.handlers`) are removed**: `BaseHandler`, `MessageHandler`, `CallbackQueryHandler` and the other 8 event classes. No real usage by users was seen. Handlers are functions (or any async callable, including an object with `async def __call__`) |
| **D15** | **All types are immutable.** `MutableTelegramObject` is gone. Changes go through builders or `obj.replace(...)` / `copy.replace(obj, ...)` (D91). (Resolves O3.) |

## 1. Types

| Item | Where | Action |
|---|---|---|
| `Message.content_type` + `ContentType` enum + `.butcher/enums/ContentType.yml` | `types/message.py:727-893`, `enums/content_type.py` | **remove**. `F.content_type == ContentType.PHOTO` → `F.photo`; `.in_({"text","sticker"})` → `F.text \| F.sticker`. Migration cost: 1 live use in docs (`docs/dispatcher/filters/magic_filters.rst:160`), 0 in examples. `send_copy` generation uses an internal content-kind table in Rust, not a public API |
| `UNSET_PARSE_MODE`, `UNSET_DISABLE_WEB_PAGE_PREVIEW`, `UNSET_PROTECT_CONTENT` | `types/base.py:33-37`, `types/__init__.py:18,774` | **remove**; `utils/media_group.py` (5 uses) switches to `Default("parse_mode")` |
| `MutableTelegramObject` (16 types) | `types/base.py:23`, `.butcher/types/*/replace.yml` | **remove** (D15) |
| `DateTime` pydantic `PlainSerializer` (+ win32 branch) | `types/custom.py` | **replace**: native datetime ↔ unix time in Rust |
| 575 `TYPE_CHECKING` `__init__` stubs, `_types_namespace` + `model_rebuild` loop | `types/**`, `types/__init__.py` tail | **remove**: generated `.pyi` replaces them (02) |
| `lru_cache` on `Update.event_type` via `utils/mypy_hacks.py` | `types/update.py:184` | **remove**: computed in Rust |
| `BotContextController` (`model_post_init`, `PrivateAttr`) and the `bot_user = Field(alias="bot")` workaround | `client/context_controller.py`, `types/managed_bot_created.py:20`, `managed_bot_updated.py:22` | **replace**: independent bound views (D103, 01 §3.2). The wire field `bot` stays exposed as `bot_user` through an overlay rename (D109, R08); it never was a plain field, because `.bot` is the bound client |
| Re-mount via `model_dump`/`model_validate` when `update.bot != bot` | `dispatcher.py:157-166` | **replace** with an O(1) new bound view (D103) |
| Bot API fields/entities deprecated in 3.x: 122 fields in 35 files (`reply_to_message_id`×18, `allow_sending_without_reply`×18, `receiver_user_id`×13, `callback_query_id`×13, 35 `Chat` fields from 7.3, `switch_pm_*` from 6.7…), types `KeyboardButtonRequestUser`, `UserShared`, `StoryAreaPosition` | generated | **remove** (ledger reset, 02 §4). Also the legacy reply params in hand-written `send_copy` (`message.py:3990, 4077-4082`) and `disable_web_page_preview=Default(...)` in `answer/reply` shortcuts (`message.py:2362, 2446`) |

## 2. Client

| Item | Where | Action |
|---|---|---|
| `Bot.__init__(**kwargs)` that only raises for `parse_mode`/`disable_web_page_preview`/`protect_content` ("removed in 3.7.0 … temporary solution") | `client/bot.py:311, 333-356` | **remove** `**kwargs` |
| Flat `link_preview_is_disabled` / `link_preview_prefer_*` / `link_preview_show_above_text` + `__getitem__` on `DefaultBotProperties` | `client/default.py:54-83` | **replace**: keep only `link_preview: LinkPreviewOptions`; `Default(...)` names follow |
| `RestartingTelegram` ("not used by Telegram anymore") | `exceptions.py:162`, `session/base.py:142-143` | **remove** → `TelegramServerError` (reason via `ErrorReason`, D47) |

## 3. Dispatcher / filters

| Item | Where | Action |
|---|---|---|
| `event_from_user` / `event_chat` / `event_thread_id` injection; `event_business_connection_id` documented but never set | `middlewares/user_context.py:52-58`, `middlewares/data.py:42-56` | **remove** (D12); `utils/i18n/middleware.py:129` → `event_context.user` |
| `CancelHandler` (2017 v2 relic, never raised) | `event/bases.py:29`, `error.py:28` | **remove** |
| `REJECTED` (nothing returns it; `pragma: no cover` branch) | `event/bases.py:22`, `router.py:200` | **remove** |
| `UnsupportedKeywordArgument` ("register filters like in 2.x") | `event/telegram.py:66-77` | **remove** → plain `TypeError` |
| `Recommendation` warning for `from magic_filter import F` | `event/handler.py:89-98`, `utils/warnings.py` | **remove** the warning, add a docs note (the `MagicFilter.as_()` subclass stays) |
| `BaseFilter = Filter` alias | `filters/__init__.py` | **remove** |
| Class-based handlers: `aiogram/handlers/` (11 files, 255 lines: `BaseHandler`, `BaseHandlerMixin`, `MessageHandler`, `CallbackQueryHandler`, `ChatMemberHandler`, `ChosenInlineResultHandler`, `ErrorHandler`, `InlineQueryHandler`, `PollHandler`, `PreCheckoutQueryHandler`, `ShippingQueryHandler`) | `aiogram/handlers/**`, special case `issubclass(callback, BaseHandler)` in `dispatcher/event/handler.py:14,115` | **remove** (D42). Also `tests/test_handler/` (11 files), the `BaseHandler` cases in `tests/test_dispatcher/test_event/test_handler.py`, and `docs/dispatcher/class_based_handlers/` (11 pages + toctree). Migration: turn the class into an `async def` handler; `self.event` / `self.data` / `self.bot` become the event argument, kwargs and `bot` |
| `dp["k"] = v` / `del dp["k"]` | `dispatcher.py:109-119` | **remove writes** (03 §3); keep reads; set data via `Dispatcher(**kw)` / `workflow_data` before start |

## 4. Utils

| Item | Where | Action |
|---|---|---|
| `aiogram.utils.markdown` | `utils/markdown.py` | **remove** (D13); rewrite 3 example files (9 uses) |
| `ContextInstanceMixin`, `DataMixin` | `utils/mixins.py` | **remove**; `I18n` uses one module-level `ContextVar` |
| deprecated `parameter=` of `create_channel_bot_link` | `utils/link.py:63-97` | **remove** |
| `deep_linking` re-exports of `create_telegram_link`/`encode_payload`/`decode_payload` | `utils/deep_linking.py:3-11` | **remove** |

| `ChatMemberAdapter` (pydantic `TypeAdapter`) | `utils/chat_member.py` | **replace** with the Rust union decoder |
| `serialization.py` (fake Bot + `model_dump`) | `utils/serialization.py` | **replace** implementation, keep the API |
| `WebAppUser`/`WebAppChat`/`WebAppInitData` hand-written pydantic models | `utils/web_app.py` | **replace**: frozen dataclasses (not Bot API types, so not butcher) |

### `CallbackData` without pydantic (D14)

Same declaration syntax, so most user code keeps working:

```python
class Item(CallbackData, prefix="item"):
    id: int
    kind: ItemKind          # Enum
    page: int | None = None
```

- Implementation: Python, `typing.dataclass_transform` for type checkers, a small converter table built at
  class creation (`int`, `str`, `float`, `bool`, `Decimal`, `UUID`, `Enum`/`IntEnum`/`StrEnum`, `X | None`,
  `Literal`), plus defaults. `pack`/`unpack` and the 64-byte limit work as today. `filter()` and the magic `F`
  rule are unchanged. Revised by PD-36 (F-08 plan-10): `CallbackData` builds on the shared `ModelBase` and its
  positional flat schema (one resolver with `FSMData`, two schemas); `rename=` and `Key` raise `TypeError` there.
- ~~No Rust: pack/unpack cost (2–3 µs) is the user's field conversion~~ — revised by PD-36: the shared converter
  core converts in Rust (unpack 0.58 µs; 1.24 µs in its first, pure-Python version), Rust-only since PyPy is dropped.
  The prefix fast-fail (09 #16) still removes most of the filter cost.
- Breaks: pydantic `Field(...)`, validators and `model_*` methods on user `CallbackData` classes. The migration
  guide shows how to replace a validator with a `__post_init__` check.

### No pydantic dependency (D14)

- aiogram declares no pydantic dependency, required or optional (no `aiogram[pydantic]` extra).
- The Rust types' `__get_pydantic_core_schema__` / `__get_pydantic_json_schema__` hooks import pydantic lazily.
  They work when the user's own project installs pydantic and cost nothing otherwise. aiogram pins no
  pydantic range, so the hooks must stick to the stable `core_schema` API.
- The serialization API is aiogram's own (`to_json` / `to_dict` / `from_*` / `replace`, D91) and doesn't need pydantic; `model_*` remain as deprecated aliases with the exact behaviour listed in 01 §3.7 (R06): `model_dump_json()` returns `str` with wire names, `model_extra` holds unknown fields only, `exclude_unset` is supported, `model_copy(update=…)` validates.
- Consequences: lower import time and RSS, one fewer free-threading dependency (pydantic-core ships only 3.14t+),
  and no `pydantic<2.15`-style upper pins on aiogram itself.

## 5. FSM

| Item | Where | Action |
|---|---|---|
| `MongoStorage` (motor), docstring "DEPRECATED … will be removed"; `PyMongoStorage` already replaced it | `fsm/storage/mongo.py:17`, `pyproject.toml:66` | **remove** class, tests (`test_mongo*.py`), `motor` / `motor-types` deps |

## 6. Webhook

Nothing legacy. `aiohttp_server.py:176` `model_dump` call moves to the native API (`to_json()` / raw bytes, R06, 05 §2.4).
Replies stay JSON for methods without files and multipart otherwise (R18).

## 7. Docs & tests

- `docs/migration_2_to_3.rst` (1 527 lines) + uk_UA `.po`: move to an archived 3.x section; write
  `migration_3_to_4.rst` listing everything in this doc plus README "Breaking changes".
- `tests/deprecated.py` `check_deprecated`: 0 callers, so **remove**.
- Compat-only tests are deleted with their features: `test_mixins.py`, `test_mongo.py` + `test_mongo_mock.py`,
  the bot-kwargs cases (`test_bot.py:64-66`), the deprecated-param cases
  in `test_link.py`, the Recommendation case in `test_handler.py`, the `event_from_user` cases in `test_user_context.py`,
  and the `UNSET_*` cases in `test_base_session.py` / `test_default.py`.

## 8. Considered and kept

`ExceptionTypeFilter`/`ExceptionMessageFilter`, `MagicData`; `handle_as_tasks`, `tasks_concurrency_limit`,
`resolve_used_update_types`, and `UNSET` for `allowed_updates` (`None` means something different);
`InaccessibleMessage`/`MaybeInaccessibleMessage` and `as_reply_parameters` (API 7.0+); `from_user`
(Python keyword); `ParseMode.MARKDOWN` (still a Bot API mode); `send_copy` (only its legacy params go);
`get_url`, `html_text`/`md_text`, `ChatActionSender`, `CallbackAnswerMiddleware`, `MediaGroupBuilder`, keyboard builders,
`deep_linking.create_*`, `auth_widget`, `web_app_signature`, the `I18n` middlewares, `backoff`, `loggers`;
`aiogram/__init__.py` exports (`html`, `md`, `F`, `flags`); `Default` + `DefaultBotProperties` (the 3.4 replacement);
`force_reply` on the keyboard builders' `as_markup` (a real field of `InlineKeyboardMarkup` and `ReplyKeyboardMarkup`
since Bot API 10.4, aiogram 3.32, #1954; PD-32);
`Dispatcher.storage`, `parent_router` (single parent; with several parents use `parent_routers`, D56); `Bot.context()` (used in multi-bot setups).
