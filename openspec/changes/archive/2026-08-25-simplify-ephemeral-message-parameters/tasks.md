## 1. Helper

- [x] 1.1 Add `Message.as_ephemeral_message_parameters(callback_query_id=None, replace_callback_query_message=None)` to `aiogram/types/message.py`, next to `as_reply_parameters`, returning `EphemeralMessageParameters | None` and preserving the current `self.from_user.id` / `self.ephemeral_message_id` condition
- [x] 1.2 Confirm `from .ephemeral_message_parameters import EphemeralMessageParameters` stays a module-level import (the value is constructed at runtime, so it must not sit under `TYPE_CHECKING`)

## 2. Generator config

- [x] 2.1 In `.butcher/types/Message/aliases.yml`, replace the inline conditional in the `reply` fill with `self.as_ephemeral_message_parameters()`
- [x] 2.2 Stop applying that fill to `reply_dice`, `reply_poll`, `reply_game`, `reply_invoice`, `reply_media_group` and `reply_paid_media` — the six whose target method has no `ephemeral_message_parameters` field. Give them a `fill` anchor without the key rather than editing generated output
- [x] 2.3 Regenerate: `.hatch/dev/bin/butcher apply all` (or from butcher's own venv with its `.env` sourced), then `uv run ruff format aiogram`
- [x] 2.4 Re-run `butcher apply all` a second time and confirm an empty diff, proving the hand-written helper survives regeneration

## 3. Tests

- [x] 3.1 Update the existing ephemeral reply tests in `tests/test_api/test_types/test_message.py` to go through the helper
- [x] 3.2 Cover the helper directly: ephemeral message returns the object; regular message returns `None`; both optional arguments land on the result
- [x] 3.3 Assert the six excluded shortcuts produce a method object with no `ephemeral_message_parameters` in fields or `model_extra`, when called on an ephemeral message
- [x] 3.4 Add a guard test that cross-checks the exclusion list against `model_fields` of each target method, so it fails if a future Bot API version adds the field to one of the six

## 5. Deprecated parameter positions

- [x] 5.1 Add `receiver_user_id` to `ignore: &ignore-reply` so `reply_*` keeps its pre-10.3 signature, and leave `callback_query_id` alone since it was already accepted there
- [x] 5.2 Add a regression test asserting `receiver_user_id` is absent from and `callback_query_id` present in the `reply_*` signatures

## 4. Ship

- [x] 4.1 Add `CHANGES/<pr>.bugfix.rst` describing the parameter that was being sent to methods which do not accept it
- [x] 4.2 Run the gate: `uv run ruff check --preview aiogram examples`, `uv run ruff format --check aiogram tests scripts examples`, `uv run mypy aiogram`, `uv run pytest tests`
- [x] 4.3 Confirm coverage of the new helper is 100%
