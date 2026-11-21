# C-15 — `_BotMethods` mixin emitter

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-09](C-09-resolution-passes.md), [C-10](C-10-ledger-diff.md) |
| Blocks | [D-01](../D-client/D-01-default-bot-properties-and-bot-cleanup.md), [C-23](C-23-check-offline-determinism.md) |
| Gate-conditional | no |
| Decisions | D100, D6c, D11, PD-02, PD-23 |
| Sources | [02-butcher.md §4, §5, §5.1 (Bot bullet)](../../research/02-butcher.md), [01-models.md §3.4](../../research/01-models.md), [11-removals.md §2](../../research/11-removals.md), `aiogram/client/bot.py` (3.x) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Today legacy butcher rewrites `aiogram/client/bot.py` in place with libcst: about 190 generated `async def` methods
mixed with hand-written code (`__init__`, context manager, `download`, the 3.7 `**kwargs` guard). In 4.0, `Bot` stays
Python, and the generated wrappers move to a separate, fully regenerated module that `Bot` inherits from, so `bot.py`
needs no markers (02 §5.1). Every wrapper is keyword-only (D100).

## Scope

**In:** `crates/butcher/src/emit/bot_methods.rs` → `aiogram/client/_bot_methods.py`:
- `class _BotMethods:` with one method per IR method:
  `async def send_message(self, *, chat_id: ChatIdUnion, text: str, parse_mode: str | Default | None = Default("parse_mode"), …, request_timeout: int | None = None) -> Message`.
  The body builds the method object and calls `await self(call, request_timeout=request_timeout)`, matching the 3.x body shape.
- Inline type annotations, so no stub is needed. Docstrings from the IR (`:param …:` / `:return:` and the source URL).
- Ledger deprecations: a parameter or method kept by the ledger gets `@deprecated` plus the docstring note.
- **Old-param translation** from ledger `replacement` entries (02 §4): the emitter path exists and is tested on a
  fixture ledger. On dev-4.x the ledger is empty (4.0 reset), so it emits nothing (see Decide item).
- No `**kwargs` on wrappers (PD-23; D99 unknown params go through the method object or `bot.call`, D96).

**Out:** the hand-written `Bot` class cleanup (`DefaultBotProperties`, removal of the 3.7 `**kwargs` guard, the
`_BotMethods` base): D-01.

## Checklist

- [ ] Template and emitter; imports computed from the IR.
- [ ] Ledger deprecation rendering.
- [ ] **Decide the old-param translation scope** (proposed default: implement only the emitter path with a fixture test.
  No runtime translation table ships while the ledger is empty; the first post-4.0 `replacement` entry exercises it).
  Record it in Notes and flag it to the owner.
- [ ] Generated test: every IR method has exactly one wrapper, and its parameter set equals the method class constructor's.
- [ ] mypy: `bot.send_message(1, "hi")` is a type error and `bot.send_message(chat_id=1, text="hi")` is OK (`tests/typing` (directory from B-01; create if absent)).
- [ ] Migration-registry entry (PD-13): D100 positional → keyword (verify the A-11 seed; the I-18 codemod rewrites it). Changelog fragment.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- `inspect.signature(Bot.send_message)` shows only keyword-only params after `self`.
- The wrapper count equals the IR method count (193 at 10.4 minus none removed), checked by a test.
- A fixture ledger `replacement` entry produces a translation that maps the old kwarg to the new one and warns once with `AiogramApiDeprecationWarning`.
- Two runs emit byte-identical output.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| libcst in-place merge into `bot.py` | Markers, merge bugs, hand-edited generated files | 02 §1, §5.1 |
| Positional parameters | Keyword-only | D100, PD-02 |
| `**kwargs` passthrough on wrappers | Typos invisible | PD-23 |

## Validation

```bash
cargo test -p butcher emit_bot_methods
cargo xtask butcher emit && make dev
uv run mypy aiogram tests/typing
uv run pytest tests/test_api/test_client
cargo xtask butcher check
```

## Workflow notes

- D-01 makes `Bot` inherit `_BotMethods` and removes the generated methods from `bot.py`. This file can land first, unused.

## Notes
