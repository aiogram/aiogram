# E-10 — Typed flag specs (`@flag_spec`)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-04](E-04-router-graph-multi-parent-flags.md) |
| Blocks | [E-21](E-21-e-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D57, D58 |
| Sources | [03-routing.md §5 "Router API and flags"](../../research/03-routing.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Flags today are untyped strings and values (`aiogram/dispatcher/flags.py`: `FlagGenerator`, `FlagDecorator`,
`get_flag`, `check_flags`); a typo in `flags.throtle(...)` silently creates a new flag and middlewares read untyped
values. D58 adds optional typed specs without breaking string flags.

## Scope

**In:**
- `flag_spec` decorator in `aiogram.dispatcher.flags` (re-exported from `aiogram`): turns a class into a frozen
  dataclass and registers it under its snake-case name (`Throttle` → `throttle`) or `name=`.
- A spec instance works as a handler decorator (`@Throttle(rate=1)`) and in `Router(flags=[Throttle(rate=2)])` (E-04
  merge rules, nearest wins).
- `flags.throttle(rate=1)` (the `FlagGenerator` path) is validated against a registered spec at registration and
  stores the spec instance.
- `get_flag(data, Throttle) -> Throttle | None` (typed overload); `get_flag(data, "throttle")` keeps working and
  returns the stored value.
- Plain string flags and unknown names stay allowed.

**Out:**
- Router-level flag merge itself (E-04).

## Checklist

- [ ] `flag_spec` + process-wide spec registry (name collision → `ValueError` at class creation).
- [ ] Decorator form, `Router(flags=[...])` form, `flags.<name>(...)` validation.
- [ ] `get_flag` overloads; `check_flags` unchanged for strings.
- [ ] Typing tests (`assert_type(get_flag(data, Throttle), Throttle | None)`).
- [ ] Docs: flags page section.
- [ ] Changelog fragment (`feature`).

## Acceptance criteria

- `flags.throttle(rat=1)` raises `TypeError` at registration when `Throttle` is a spec.
- 3.x flag tests (`tests/test_flags/`) pass unchanged.
- mypy infers the spec type from `get_flag(data, Throttle)`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Mandatory typed flags | Breaks all string flags | D58 |
| pydantic models as specs | pydantic is not a dependency | D14 |

## Validation

```bash
make dev
uv run pytest tests -q
make lint
uv run mypy aiogram
```

## Workflow notes

- G-13 / G-14 middlewares may define their flags as specs; coordinate names.

## Notes
