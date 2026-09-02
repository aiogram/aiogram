---
name: aiogram-add-shortcut
description: Add or change a shortcut method on a Bot API type (Message.answer_*, reply_*, ChatMemberUpdated/CallbackQuery helpers) or a Default() sentinel, through .butcher config rather than hand-edited generated code. Use when asked to "add a shortcut", "add .answer_x", "forward a parameter to the shortcut", or to wire a bot-level default onto a field.
---

# Add a shortcut through `.butcher`

Explicit maintainer feedback in `AGENTS.md`: *"shortcuts/features should be added
through `.butcher` config + generation, not ad-hoc manual edits."* A shortcut written
straight into `aiogram/types/*.py` disappears at the next `butcher apply all`.

## Where shortcuts are declared

`.butcher/types/<Type>/aliases.yml` — 11 such files exist; `Message` is the big one.

```yaml
answer:
  method: sendMessage
  code: &assert-chat |
    assert self.chat is not None, "This method can be used only if chat is present in the message."
  fill: &fill-answer
    chat_id: self.chat.id
    message_thread_id: self.message_thread_id if self.is_topic_message else None
    business_connection_id: self.business_connection_id

reply:
  method: sendMessage
  code: *assert-chat
  fill: &fill-reply
    <<: *fill-answer
    reply_parameters: self.as_reply_parameters()
  ignore: &ignore-reply
    - reply_to_message_id
```

Keys: `method` (Bot API method name, camelCase), `fill` (params auto-filled from the
carrier object — expressions are inlined verbatim), `ignore` (params dropped from the
shortcut signature), `code` (a guard prepended to the body). YAML anchors are used
heavily — reuse `*fill-answer` / `*fill-reply` / `*ignore-reply` instead of copying.

Related config in the same directory: `default.yml` maps a field to a bot-level
default sentinel (`parse_mode: parse_mode` → `Default("parse_mode")`), `replace.yml`
overrides annotations, `subtypes.yml` / `unions.yml` wire union membership.

## Procedure

1. Edit `.butcher/types/<Type>/aliases.yml` (or `default.yml`). Mirror the closest
   existing entry; do not invent a new shape. Never touch `entity.json`.
2. Regenerate if you can:
   ```bash
   rtk proxy uv run --extra cli butcher apply all
   ```
   **`butcher` is not installed in this checkout** (`Failed to spawn: butcher`) — it is
   maintainer-only. When it is unavailable, hand-write the identical output into
   `aiogram/types/<snake>.py` (and `aiogram/client/bot.py` if the method itself
   changed), matching the surrounding generated style exactly, and say in the PR body
   that regeneration was not run locally. Config and output must never disagree.
3. Watch the default sentinels. A shortcut parameter declared `= None` **overrides**
   the model's `Default(...)` — that was bug #1873 across 13 entities. Forward
   `Default("parse_mode")`, not `None`, unless there is a stated reason
   (`Message.send_copy` deliberately keeps `None`).
4. Test it in `tests/test_api/test_types/test_<type>.py`: `bot.add_result_for(<Method>, ...)`,
   call the shortcut, `bot.get_request()`, assert every filled field. If it forwards a
   parameter with a fallback (like `link_preview_options` in `send_copy`, #1797), assert
   both the explicit and the fallback branch.
5. `CHANGES/<issue>.feature.rst` (or `.bugfix.rst` if it restores broken behavior),
   describing the shortcut with ``:meth:`aiogram.types.message.Message.answer_x` ``.
6. Checks:
   ```bash
   rtk ruff format aiogram tests scripts examples
   rtk ruff check --show-fixes --preview aiogram examples
   rtk mypy aiogram
   rtk test uv run pytest tests -q
   ```

Docs need nothing extra — `docs/api/types/*.rst` is generated from
`.butcher/templates/types/entity.rst.jinja2` and picks members up via `automodule`.
