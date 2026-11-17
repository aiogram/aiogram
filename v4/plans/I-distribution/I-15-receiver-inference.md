# I-15 — Receiver inference for the migrate tools

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-14](I-14-migrate-engine.md), [C-26](../C-butcher/C-26-removal-inventory-signature-table.md) |
| Blocks | [I-17](I-17-model-semantics-rules.md), [I-18](I-18-positional-to-keyword-rule.md) |
| Gate-conditional | no |
| Decisions | D100, D101, D103, D106, PD-02, R28 |
| Sources | [16-support-policy.md §2.2–2.3](../../research/16-support-policy.md), [01-models.md §3.4](../../research/01-models.md), [codex-review R28](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Several rules need to know what a receiver is:
- the positional→keyword rewrite (D100, kept by PD-02);
- bare `x.as_(bot)` statements (D103);
- list comparisons on collection fields (D106);
- mutation rewrites (D15).

16 §2.2 resolves `bot.*` through `Bot` annotations, and shortcuts on `Message` / `CallbackQuery` / … "where the
receiver type can be inferred (handler parameter annotations, `isinstance`)".

The most common line in a 3.x bot is `message.answer("hi")` inside a handler that is often **unannotated**
(`async def h(message)`). The decorator `@router.message(...)` already fixes the event type, so this plan adds
**observer-decorator inference** on top of 16's sources. That decides how much of D100 is fixable automatically.

The 3.x positional order and the shortcut-name → type map come from C-26's 3.x signature table.

## Scope

**In:**
- **Inference sources, in priority order:**
  1. explicit annotations on parameters, variables and returns (`message: Message`, `bot: Bot`), including
     `Optional` / `|` unions of aiogram types;
  2. `isinstance(x, T)` narrowing within the guarded block;
  3. **observer decorators:** a function decorated with `@<router>.<observer>(...)` or registered via
     `<router>.<observer>.register(fn, ...)` gets its first positional parameter typed from the observer (`message` →
     `Message`, `callback_query` → `CallbackQuery`, `edited_message` → `Message`, …, from the C-26 table). Here
     `<router>` is any name bound to `Router(...)` / `Dispatcher(...)` or annotated as such;
  4. a `bot` parameter name or a `Bot(...)` construction gives `Bot`;
  5. attribute chains from a known receiver (`message.chat` → `Chat`, `callback_query.message` →
     `MaybeInaccessibleMessage`, from the C-26 field table).
- **Confidence levels.** High for 1 to 2, medium for 3 to 5. An unresolved receiver gives `None`, and the rule reports
  instead of rewriting.
- **Alias tracking** for imports (`from aiogram import Router as R`) and simple assignments (`r = Router()`).
- **API.** `infer(node) -> Inferred(type_name, confidence, source)`, used by I-17 and I-18.
- **C-26 table.** A versioned data file (from C-26) loaded by path, with the 3.x source version recorded. The engine
  prints the table's 3.x version in `--format json` metadata.

**Out:**
- The rewrites themselves (I-17, I-18).
- A full type checker (no mypy or pyright dependency).

## Checklist

- [ ] `aiogram/migrate/infer.py` with the five sources and confidence.
- [ ] Load C-26's table: confirm its path and format with C-26. Record the 3.x version it was generated from.
- [ ] **Decide which 3.x version the table tracks** (proposed default: the migration-baseline 3.x release cut by
      3x-24. Bot API bumps after it only append parameters at the end (3.x `keep_position`), so the baseline order is a
      prefix of later orders and stays correct for positional calls. C-26 regenerates the table if a 3.x release ever
      reorders). Record it in Notes and flag it to the owner.
- [ ] Observer → event-type map covering every 3.x observer (C-26's observer → event-type table),
      tested for completeness against the 3.x `aiogram/dispatcher/router.py` observer list.
- [ ] Golden tests: annotated handler, unannotated decorated handler, `register(...)` form, `isinstance` block, aliased
      imports, nested function shadowing a name (must not infer), `lambda` (none).
- [ ] Tests (100% coverage of `infer.py`).
- [ ] No changelog fragment (internal to I-14's feature); no registry entry.

## Acceptance criteria

- On the golden corpus each case infers the expected type and confidence. A shadowed name and an unknown receiver both
  return `None`.
- `async def h(message)` decorated with `@router.message(F.text)` infers `Message` at medium confidence.
- The table's 3.x version appears in JSON output metadata.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Running mypy/pyright for types | Heavy dependency, needs the user's environment | R28 (conservative fallbacks), D74 |
| Name-only heuristics (`message` → `Message`) without a decorator | Too many false positives; at most a low-confidence heuristic | R28 |
| Importing aiogram 3.x to read signatures | Tools run in the 4.x environment; table from C-26 | D74 |

## Validation

```bash
make dev
uv sync --extra migrate
uv run pytest tests/test_migrate -q
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: I-14 (rule API), C-26 (3.x signature/field/observer table).
- Outputs: `infer()`, used by I-17 and I-18.

## Notes

(empty)
