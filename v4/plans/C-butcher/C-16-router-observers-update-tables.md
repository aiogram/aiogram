# C-16 — Router observers mixin and update tables (Python)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-09](C-09-resolution-passes.md) |
| Blocks | [E-05](../E-runtime/E-05-typed-observers-unknown-update.md), [E-09](../E-runtime/E-09-routing-keys-compiled-rejectors.md), [H-11](../H-testing-observability/H-11-generated-toolkit-tables.md), [C-23](C-23-check-offline-determinism.md) |
| Gate-conditional | no |
| Decisions | D55, D12, D10, B14 |
| Sources | [03-routing.md §3, §5 (Router API defaults)](../../research/03-routing.md), [02-butcher.md §5](../../research/02-butcher.md), [11-removals.md §1, §3](../../research/11-removals.md), [14-testing.md §3](../../research/14-testing.md), `aiogram/dispatcher/router.py`, `aiogram/dispatcher/middlewares/user_context.py` (3.x) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Every Bot API update type is currently hand-wired in three places:
- `Router.__init__` (`aiogram/dispatcher/router.py`) lists `self.message = TelegramEventObserver(router=self, event_name="message")` and the others by hand;
- `UserContextMiddleware.resolve_event_context` (`aiogram/dispatcher/middlewares/user_context.py`) maps each update type to user/chat/thread;
- `Update.event_type` (`aiogram/types/update.py`) is a hand-written chain.

D55's defaults generate observers from the IR as a `_RouterObservers` mixin, typed as `TelegramEventObserver[Message]`.

## Scope

**In:** `crates/butcher/src/emit/dispatch.rs`:
- `aiogram/dispatcher/_router_observers.py`: `class _RouterObservers:` with typed attribute declarations and an
  `_init_observers(self)` that creates one `TelegramEventObserver[T]` per `Update` field (event name = wire key), plus
  an `observers` mapping in IR order. `errors`, `unknown_update` (10 §3) and `runtime_errors` (D50) are not Bot API
  update types; E-05 declares them by hand.
- `aiogram/dispatcher/_event_context_table.py`: per update type, the overlay `events.toml` paths for
  `user`/`chat`/`thread_id`/`business_connection_id`. E-05/E-09 build the D12 `event_context` resolution from it.
- `aiogram/_generated/content_kinds.py`: the Python content-kind table (overlay `content.toml`) for E-05 and the
  testing toolkit's posted-content table (H-11) only. The Rust table behind `routing_keys()` (E-09) is C-19's.
- Typing: `tests/typing` (directory from B-01; create if absent) case `@router.message()` on a handler taking `CallbackQuery` is a mypy error.

**Out:** `Router` using the mixin and the hand list removed (E-05); the Rust-side `Update.event_type` (C-19, see Decide
item); toolkit tables beyond content kinds (H-11).

## Checklist

- [ ] Emitters for the three files; imports computed from the IR.
- [ ] **Decide where `event_type` lives** (02 §5 lists `Update.event_type` among the Python-emitted sites, 11 §1 says "computed in Rust"). Proposed default: `Update.event_type` / `event` in **Rust** (C-19), and the event-context table in **Python** (this task). Record it in Notes and flag it to the owner.
- [ ] Test: the observer set equals the IR `Update` field set (minus `update_id`), and each observer's type parameter is the field's type.
- [ ] Test: every update type has an `events.toml` entry (possibly empty); a new type without one fails `check` (C-23 rule).
- [ ] Migration-registry entry (PD-13): none (no user-visible change; D12's removal entry belongs to E-01).
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- The emitted observer list matches today's hand list in `Router.__init__` for 10.4 (same names, same order) plus any update types the IR adds.
- The event-context table reproduces `resolve_event_context`'s outputs on the 3.x test cases (`tests/test_dispatcher/test_middlewares/test_user_context.py`).
- Two runs emit byte-identical output.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Hand list in `router.py` | Bot API bump step that drifts | D55 defaults |
| Router-level filter | Per-observer `.filter()` only | D55 |
| Public `ContentType` for content kinds | Removed; internal table only | 11 §1 |

## Validation

```bash
cargo test -p butcher emit_dispatch
cargo xtask butcher emit && make dev
uv run mypy aiogram tests/typing
uv run pytest tests/test_dispatcher
cargo xtask butcher check
```

## Workflow notes

- E-05 consumes the mixin and the Python content-kind table, E-09 the event-context table (its content kinds come
  from C-19's Rust table via `routing_keys()`), H-11 the content-kind table.

## Notes
