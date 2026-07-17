---
name: test-bot-api-codegen
description: Add tests for a freshly codegenerated Bot API update in aiogram, and catch the hand-written call sites butcher never touches. Use after `butcher apply all` / `make update-api`, when the user says "add tests for the new Bot API changes", "cover the codegen", or when a Bot API bump branch needs to reach 100% coverage.
---

# Test a Bot API codegen run

`butcher` generates types, methods, enums and the router observers. It does **not**
touch several hand-written files that enumerate Bot API concepts, and its enum
parser can emit silently-wrong members. Tests written before those are fixed will
lock the bugs in — so **fix the source first, then test**.

Coverage goal for this repo is **100%**.

## 1. Scope the change

```bash
git diff --stat HEAD -- aiogram/
git status --short -- aiogram/            # new files = new types/methods/enums
```

Then get ground truth — the uncovered lines *are* the to-do list:

```bash
uv run pytest tests -q --cov=aiogram --cov-report=term-missing
```

Note the failures too: this repo has guard tests that fail on purpose when new
Bot API entities lack examples (see step 3).

## 2. Fix what codegen missed (before writing any test)

### Hand-written sites that enumerate update types

A new `Update.<field>` needs all three of these, or the update is dead on arrival —
the generated observer in `router.py` can never fire:

| File | What to add | Symptom if missed |
|---|---|---|
| `aiogram/types/update.py` → `event_type` | `if self.<field>: return "<field>"` before the `raise` | `UpdateTypeLookupError`, "Detected unknown update type" |
| `aiogram/dispatcher/middlewares/user_context.py` → `resolve_event_context` | an `EventContext(...)` branch before the final `return EventContext()` | `event_from_user` / `event_chat` silently absent in handlers |
| `aiogram/dispatcher/router.py` | *generated* — verify only | — |

Mirror the nearest existing branch (e.g. `managed_bot` for a user-only update).
To confirm you found every such site, grep for the most recently added update
type and see which non-generated files mention it:

```bash
git grep -n guest_message -- aiogram | grep -v 'aiogram/\(types\|methods\|enums\)/'
```

### Enums parsed from the docs by regexp

`.butcher/enums/*.yml` scrape members out of a doc sentence. When the regexp does
not match the doc's quoting style it yields **garbage members copied from another
enum**, not an error. Always eyeball a new enum against the docstring of the
attribute it was parsed from:

```bash
cat aiogram/enums/<new_enum>.py
```

If the members look like they belong to a different type, fix the `regexp:` in
`.butcher/enums/<Name>.yml` — `"'([a-z_]+)'"` is the form used for quoted values,
`'\*([a-z_]+)\*'` only for bolded ones — and correct the generated file. Flag it
so `butcher parse` can be re-run to confirm it regenerates identically.

Also run the `fix-codegen-imports` skill if ruff reports F821.

## 3. Where each kind of change gets tested

| Codegen change | Test location | Pattern to mirror |
|---|---|---|
| New method + `Bot` shortcut | one new `tests/test_api/test_methods/test_<snake>.py` | `test_edit_message_text.py` — `add_result_for` → `await bot.<method>(<required args only>)` → `bot.get_request()` → assert |
| New `Message` service field / `ContentType` | `tests/test_api/test_types/test_message.py` | add a `TEST_MESSAGE_<NAME>` constant, then register it in **both** `MESSAGES_AND_CONTENT_TYPES` and `MESSAGES_AND_COPY_METHODS` (`None` for service messages) |
| New `Update` type | `tests/test_dispatcher/test_dispatcher.py` + `test_router.py` | a `pytest.param` in `test_listen_update`'s parametrize `(event_type, update, has_chat, has_user)`, plus an `observers[...]` assertion in `test_observers_config` |
| New discriminated union (`*Union` with `Field(discriminator=...)`) | `tests/test_issues/test_1842_rich_block_union_discriminator.py` | invalid-tag → single `union_tag_invalid`; nested resolution; depth-30 non-exponential guard |
| New plain type with no shortcuts/logic | nothing | import-time coverage is enough; do not add a test file |

`TestAllMessageTypesTested` in `test_message.py` fails until every `ContentType`
member has an example message — that failure is the spec, not a flake.

Most types have no test file at all. Only add one when the type carries behavior.

## 4. Verify

```bash
uv run ruff format aiogram tests scripts examples
uv run ruff check --show-fixes --preview aiogram examples
uv run mypy aiogram
uv run pytest tests -q --cov=aiogram --cov-report=term-missing
```

`TOTAL ... 100%` with zero missing lines, and no failures. Pre-existing ruff
findings under `tests/` (PLC2701 in `conftest.py`, `test_filters/`) are out of
the mandated scope — leave them.

## 5. Follow-up

Bot API bumps are CI-gated on a changelog fragment: `CHANGES/<issue>.misc.rst`.
Use the `aiogram-api-changelog` skill; it needs the issue/PR number and the
core.telegram.org changelog URL, so ask for them rather than guessing.

## Parallelising

The work partitions cleanly by test file, so independent agents can write them
concurrently without conflicting — one per bullet in the step-3 table. Do the
step-2 source fixes yourself first; every agent depends on them.
