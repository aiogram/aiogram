# E-05 — Generated typed observers and the `unknown_update` observer

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [C-16](../C-butcher/C-16-router-observers-update-tables.md), [E-03](E-03-snapshot-lifecycle.md) |
| Blocks | [E-14](E-14-feed-paths-forward-compat-dispatch.md), [E-15](E-15-poller.md), [E-21](E-21-e-exit-gate.md), [H-17](../H-testing-observability/H-17-toolkit-feature-interop.md) |
| Gate-conditional | no |
| Decisions | D55, D10, R13 |
| Sources | [03-routing.md §5 "Router API and flags"](../../research/03-routing.md), [10-forward-compatibility.md §3](../../research/10-forward-compatibility.md), [19 R13](../../research/19-review-resolutions.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`Router.__init__` hand-lists one `TelegramEventObserver` per update type, which is a manual step on every Bot API
bump. D55: generate them from the IR as a `_RouterObservers` mixin (C-16 emits it), typed so mypy checks the handler's
event parameter. 10 §3 adds `router.unknown_update` for unknown-type and undecodable updates.

## Scope

**In:**
- `Router` inherits the generated `_RouterObservers` mixin (C-16); remove the hand list in `Router.__init__`.
- `TelegramEventObserver[EventT]` generic; `@router.message()` typed as `TelegramEventObserver[Message]` (typing only).
- Keep `router.observers: dict[str, TelegramEventObserver]` with every generated observer plus `update` (dispatcher),
  `error`/`errors` and `unknown_update` — scenes register through `router.observers[name]`
  (`aiogram/fsm/scene.py`, `SceneRegistry` / `Scene` wiring).
- Hand-written `unknown_update` observer on every router (not generated, not a Bot API type); routing of shells and
  unknown types into it is E-14.
- `resolve_used_update_types()` reads the compiled snapshot (E-03); `unknown_update`, `error(s)`, `update` are never
  returned as `allowed_updates` values.

**Out:**
- The emitter itself (C-16). Dispatch into `unknown_update` and decode shells (E-14). The R13 warning about derived
  `allowed_updates` (E-15, Poller).

## Checklist

- [ ] Wire the C-16 mixin; delete the hand list; keep attribute names identical to 3.x.
- [ ] Generic `TelegramEventObserver[EventT]`; typing test with `assert_type` for 3–4 observers.
- [ ] `unknown_update` observer present on every router and in `observers`.
- [ ] `resolve_used_update_types` from the snapshot.
- [ ] Tests: observer set equals the IR update-type list + the hand-written ones; mypy rejects a `CallbackQuery`
  handler on `router.message` (typing test file under `tests/typing/` (directory from B-01; create if absent), run by mypy in CI).
- [ ] Changelog fragment (`feature`: typed observers, `unknown_update`).

## Acceptance criteria

- `cargo xtask butcher check` passes and a Bot API bump that adds an update type adds the observer with no hand edit
  (verified with a C-25 scenario fixture).
- `mypy` reports an error for a handler whose first parameter type doesn't match the observer's event type.
- `resolve_used_update_types()` output equals 3.x for the A-10 routing fixtures.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep the hand-written observer list | Manual Bot API bump step | D55 |
| Generate `unknown_update` from the IR | It is not a Bot API update type | 10 §3 |

## Validation

```bash
make dev
cargo xtask butcher check
uv run pytest tests -q
make lint
uv run mypy aiogram tests/typing        # typing assertions (directory from B-01)
```

## Workflow notes

- Consumes C-16 (mixin + update tables). Produces the observer surface E-14/E-15 and F-13 use.

## Notes
