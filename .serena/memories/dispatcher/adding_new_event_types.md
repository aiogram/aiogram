# Adding a New Update/Event Type to aiogram Dispatcher

When Telegram Bot API adds a new update type (e.g. `managed_bot`, `purchased_paid_media`), the following files must be touched. Types, enums, and butcher configs are generated — the dispatcher integration is manual.

## Checklist (in order)

### Generated / butcher layer (run `butcher parse && butcher refresh && butcher apply all`)
- `.butcher/types/<TypeName>/entity.json` — type definition
- `.butcher/types/Update/entity.json` — add field to Update entity
- `aiogram/types/<type_name>.py` — generated type class
- `aiogram/types/__init__.py` — export
- `aiogram/enums/update_type.py` — `NEW_TYPE = "new_type"` enum member
- `aiogram/types/update.py` — `new_type: NewType | None = None` field + TYPE_CHECKING import + `__init__` signature

### Manual dispatcher integration (NOT generated)

1. **`aiogram/types/update.py`** — `event_type` property (lines ~161-215): add `if self.new_type: return "new_type"` before the `raise UpdateTypeLookupError` line

2. **`aiogram/dispatcher/router.py`** — two places in `Router.__init__`:
   - Add `self.new_type = TelegramEventObserver(router=self, event_name="new_type")` after the last observer attribute (before `self.errors`)
   - Add `"new_type": self.new_type,` to the `self.observers` dict (before `"error"`)

3. **`aiogram/dispatcher/middlewares/user_context.py`** — `resolve_event_context()` method: add `if event.new_type: return EventContext(user=..., chat=...)` before `return EventContext()`. Use `user` field for user-scoped events, `chat` for chat-scoped. No `business_connection_id` unless the event has one.

### Tests (manual)

4. **`tests/test_dispatcher/test_dispatcher.py`** — add `pytest.param("new_type", Update(update_id=42, new_type=NewType(...)), has_chat, has_user)` to `test_listen_update` parametrize list. Import `NewType` in the imports block.

5. **`tests/test_dispatcher/test_router.py`** — add `assert router.observers["new_type"] == router.new_type` to `test_observers_config`

### Docs (generated or manual stub)
- `docs/api/types/<type_name>.rst` — RST stub
- `docs/api/types/index.rst` — add to index

## Key invariants
- The snake_case name must be identical across: `UpdateType` enum value, `Update` field name, `event_type` return string, Router attribute name, observers dict key, and `TelegramEventObserver(event_name=...)`.
- `Update.event_type` uses `@lru_cache()` — never mutate Update fields after construction.
- The routing machinery (`propagate_event`, middleware chains, sub-router propagation) requires **zero changes** — it operates on observer names looked up dynamically.

## Example: `managed_bot` (API 9.6)
- Type: `ManagedBotUpdated` with fields `user: User` (creator) and `bot_user: User` (the managed bot)
- user_context: `EventContext(user=event.managed_bot.user)` — user only, no chat
- `has_chat=False, has_user=True` in test parametrization
