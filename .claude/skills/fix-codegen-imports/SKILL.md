---
name: fix-codegen-imports
description: Fix missing imports in butcher-generated aiogram code (F821 "Undefined name" after `butcher apply`). Use when ruff reports undefined names in aiogram/enums, aiogram/types or aiogram/methods after a Bot API codegen run, or when the user says "fix codegen imports".
---

# Fix codegen imports

`butcher apply` sometimes emits modules that reference a name it never imported
(usually a new enum, or `Enum` itself). Ruff catches all of them as F821.

## Steps

1. List the offenders:

   ```bash
   uv run ruff check --preview --output-format=concise aiogram examples
   ```

   Only `F821 Undefined name` findings are in scope. Anything else is a real bug — report it, don't patch it.

2. For each undefined name, copy the import from a sibling module that already
   uses the same kind of symbol — do not invent a new style:

   | Undefined name | Fix | Reference file |
   |---|---|---|
   | `Enum` in `aiogram/enums/*.py` | `from enum import Enum` as the first line | `aiogram/enums/chat_action.py` |
   | An enum in `aiogram/types/*.py` or `aiogram/methods/*.py` | `from ..enums import <Name>`, placed above the `from .` imports | `aiogram/types/input_paid_media_photo.py` |
   | A type in `aiogram/types/*.py` | `from .<snake_case_module> import <Name>` | any sibling type |

   If the module has annotations referencing types only imported under
   `TYPE_CHECKING`, it also needs `from __future__ import annotations` as the
   first line — generated modules that quote forward refs all have it.

3. Verify:

   ```bash
   uv run ruff format aiogram
   uv run ruff check --preview aiogram examples
   uv run mypy aiogram
   ```

## Follow-up

These files are generated. A hand-fix survives only until the next
`butcher apply all`. After the branch is green, tell the user the durable fix
belongs in `.butcher` (template / entity config for the symbol whose import was
dropped) so regeneration stops losing it.
