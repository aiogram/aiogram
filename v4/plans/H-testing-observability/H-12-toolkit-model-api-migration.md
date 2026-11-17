# H-12 — Model-API migration inside the toolkit

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-11](H-11-generated-toolkit-tables.md), [B-06](../B-spike/B-06-value-semantics-native-api.md), [C-13](../C-butcher/C-13-reexport-modules.md), [C-18](../C-butcher/C-18-rust-type-emitter.md), [D-10](../D-client/D-10-request-snapshot-and-render-hook.md), [D-12](../D-client/D-12-custom-session-hook-compatibility.md), [H-10](H-10-testing-world-import.md) |
| Blocks | [H-13](H-13-binding-identity-rewrite.md), [H-16](H-16-fake-fidelity.md), [H-17](H-17-toolkit-feature-interop.md) |
| Gate-conditional | yes |
| Decisions | D52, D91–D95, D105, D106, D108, D15, D100, PD-07, R26 |
| Sources | [14-testing.md §3 "Rewritten"](../../research/14-testing.md), [01-models.md §3.1, §3.7](../../research/01-models.md), [05-network.md §2.1, §2.3](../../research/05-network.md), [19 D105, D106, D108, R26](../../research/19-review-resolutions.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Once `aiogram.types` is the Rust-native layer (C-13/C-18), the toolkit's pydantic usage stops working:
`model_fields`, `model_copy`, `model_dump`/`model_validate`, `__pydantic_extra__`, `ContentType`, list mutation on
immutable objects, and positional constructor calls.

D52 keeps typed interception: the fake receives method objects and never runs the encoder. Two things the encoder
normally does must still happen for the fake to see what Telegram would see: `Default(...)` resolution and lazy-text
rendering (PD-07). Per the planning resolution, the fake **reuses D-10's resolve/render step** rather than a second
generated resolver.

## Scope

**In:**

| Before | After |
|---|---|
| `model_fields` | `_tables.FIELDS` (H-11) |
| `model_copy(update=…)` | `obj.replace(...)` |
| `model_dump` / `model_validate` | `to_dict()` / `from_dict(..., bot=)` (D91) |
| `__pydantic_extra__` | `obj.raw` (D108: fresh dict per access) |
| `ContentType` | `_tables.POSTED_CONTENT` |

- **Immutability** (D15): every `obj.field = value` in `world.py`, `actors.py`, `modeling.py` and `overrides.py`
  becomes `replace` and re-store in the world.
- **Collection fields are tuples** (D106): stored tuples, tuple comparisons, no `.append` on API objects. World-side
  bookkeeping lists (`chat.messages`) stay Python lists of world state.
- **Keyword-only calls** (D100) for all generated constructors and methods used by the toolkit.
- **Default + lazy text:** `FakeTelegramSession.make_request` passes each intercepted method through the D-10 step
  (resolved against `bot.default`, lazy text rendered with the captured i18n context, PD-07) before `handle_call`.
  Models therefore see final values, never `Default(...)` or a `LazyProxy`.
- Result synthesis (`synthesis.py`) builds results from `_tables.RETURNS` / `FIELDS` with the keyword-only
  constructors. Unknown-field attribute access (D105 deprecation) is not used anywhere in the toolkit.
- `deserialize_telegram_object`-style helpers used by assertions move to the native API.

**Out:**
- Binding/`mounting.py` and the five `as_(` uses (H-13).
- Runner delivery (H-14).
- R26 marks and trace replay (H-16).
- i18n-specific interop tests (H-17).

## Checklist

- [ ] Replace every pydantic API use in `aiogram/test/**`. A guard test greps that `model_fields`, `model_copy`,
      `model_dump`, `model_validate`, `__pydantic_extra__` and `ContentType` don't occur in `aiogram/test/**`.
- [ ] Immutability and tuple migration in world and actors.
- [ ] D-10 resolve/render step (D-10 exposes it as a Python-callable function returning a resolved method, not
      bytes) called in `FakeTelegramSession.make_request`. Do not write a resolver here.
- [ ] Keyword-only call sites.
- [ ] Port `tests/test_testing/**` to the same API (no behaviour changes to the asserted scenarios).
- [ ] Tests:
  - [ ] a handler sending `parse_mode=Default("parse_mode")` gets the bot default in the fake's stored message;
  - [ ] a lazy text returned from a handler is rendered in the stored message;
  - [ ] the toolkit guard grep.
- [ ] No changelog (toolkit internals), unless a toolkit public signature changes. Then add a fragment and a
      registry entry (PD-13).

## Acceptance criteria

- `uv run pytest tests/test_testing` passes on the Rust-native types with the same scenario count as after H-10
  (record the before/after counts in the PR body).
- The guard grep finds no pydantic API in `aiogram/test/**`.
- No `Default` instance and no lazy proxy ever reaches a `@models` handler (assertion hook in a test build).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Running the real Rust encoder/decoder in the fake | Codec fidelity is the codec's own tests and the D-15 differential harness; typed interception keeps the fake fast and introspectable | D52 |
| A generated Default resolver in the toolkit (14 §3) | Duplicates D-10's contract, the R26 blind spot | planning resolution |
| Keeping pydantic as a toolkit dependency | aiogram no longer depends on pydantic | D12–D15 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
cargo test        # only if a Rust helper was touched
```

## Workflow notes

- Gate-conditional: it assumes the Rust-native types (B-13 go). Re-validate after B-13.
- Inputs:
  - H-11 tables;
  - B-06 native API;
  - C-13/C-18: types wired as `aiogram.types`;
  - D-10: resolve/render step.
- Unblocks H-13 (identity), H-16 (fidelity), H-17 (interop).

## Notes
