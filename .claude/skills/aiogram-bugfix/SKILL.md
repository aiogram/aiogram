---
name: aiogram-bugfix
description: End-to-end loop for fixing a reported bug in aiogram — reproduce, fix at the root, add the regression test where this repo puts it, write the CHANGES fragment, run the exact CI checks. Use when the user references a GitHub issue number, reports broken behavior, or asks to fix/patch something in aiogram.
---

# Fix a bug in aiogram

This is the most repeated procedure in the repo: every one of the last ten bugfix
commits is the same three-part diff — **source fix + test + `CHANGES/<issue>.bugfix.rst`**.
Any of the three missing is a rejected PR (the changelog one is CI-gated).

Ask for the issue/PR number if it was not given — it names both the changelog
fragment and, when used, the regression test file.

## 1. Reproduce before editing

Write the failing assertion first. Cross-cutting bugs (DI, scenes, dispatcher,
webhook, unions) get their own file:

```
tests/test_issues/test_<issue>_<slug>.py
```

Existing examples: `test_1687_scene_goto_loses_middleware_data.py`,
`test_1741_forward_ref_in_callbacks.py`, `test_1743_channel_post_with_scenes.py`,
`test_1842_rich_block_union_discriminator.py`.

A bug local to one module goes into the nearest existing test module instead —
that is what most bugfixes do (`test_command.py`, `test_message.py`,
`test_text_decorations.py`, `test_dispatcher.py`).

Use `MockedBot` and the `tests/conftest.py` fixtures; `asyncio_mode = auto`, so no
asyncio marker. See the `aiogram-test-author` agent for the patterns.

## 2. Fix at the root, then grep the siblings

The ticket names one symptom; this repo's history is full of the sibling that was
left broken. Before you finish, check the mirror paths:

- polling vs webhook feed (`Dispatcher` vs `aiogram/webhook/aiohttp_server.py`)
- `feed_update` vs `feed_raw_update`
- `Message` vs `InaccessibleMessage` shortcuts
- one entity vs every entity with the same field (#1873 fixed 13 at once)

```bash
git grep -n <symbol> -- aiogram
```

If the file lives under `aiogram/{types,methods,enums}/` it is **generated** — the
durable fix belongs in `.butcher/**` (or is regeneration drift to be mirrored).
Hand it to the `bot-api-codegen` agent rather than patching output blindly.

## 3. Changelog fragment

`CHANGES/<issue-or-PR>.bugfix.rst`, one short paragraph of user-visible behavior,
reStructuredText, roles like ``:class:`aiogram.types.message.Message` `` and
``:code:`field` ``. No issue back-link — towncrier adds it. Do not edit `CHANGES.rst`.

Category is `bugfix` here; `feature`, `doc`, `removal`, `misc` exist for other work.

## 4. Verify exactly what CI verifies

```bash
rtk ruff format aiogram tests scripts examples
rtk ruff check --show-fixes --preview aiogram examples
rtk mypy aiogram
rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing
```

New lines must be covered — the target is 100%. Add `--redis redis://localhost:6379/0`
and `--mongo mongodb://mongo:mongo@localhost:27017` when the fix touches
`aiogram/fsm/storage/`.

## 5. Hand off

Branch off `dev-3.x`. Commit message ends with `Co-Authored-By:` only. PR body should
carry a reproduction and the validation steps you actually ran. Review with the
`aiogram-pr-gate` agent before opening it.
