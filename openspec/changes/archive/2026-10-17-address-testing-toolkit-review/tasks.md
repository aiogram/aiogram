# Tasks

## 1. Anonymous binding

- [x] 1.1 Check the binding once as a trigger starts (design D1); verify an anonymous administrator can demote or promote themself, and the next trigger raises
- [x] 1.2 Refuse the person-only triggers from a bot (design D2); verify each raises and feeds nothing
- [x] 1.3 Refuse an anonymous vote in a poll of another chat (design D6); verify a hand-stored poll is not refused

## 2. Update delivery

- [x] 2.1 Adopt the update a withheld trigger returns (design D3); verify `answer()` works on it and the task snapshot is taken
- [x] 2.2 Keep `me()` in step with `getMe` (design D5); verify it makes no call

## 3. Flood and forwarding

- [x] 3.1 Count every message of an album or a batch (design D4); verify two albums of ten fill a group's minute and a missing reply still answers 400
- [x] 3.2 Check the chat and the thread once per forward or copy call (design D7); verify a batch runs each check once

## 4. Docs and integration

- [x] 4.1 Document the changes in `docs/dispatcher/testing.rst` and `CHANGES/1887.feature.rst`
- [x] 4.2 Run `make lint`, `uv run pytest tests` with `aiogram/test` at 100% coverage, the docs build and `openspec validate --all --strict`; verify all pass with no new warnings
