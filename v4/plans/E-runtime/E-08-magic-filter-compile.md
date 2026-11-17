# E-08 — Compile `F` expressions to closures

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-07](E-07-sync-filter-execution.md) |
| Blocks | [E-09](E-09-routing-keys-compiled-rejectors.md), [E-21](E-21-e-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D37, D70, R10 |
| Sources | [03-routing.md §3, §5 D37](../../research/03-routing.md), [codex-review R10](../../research/codex-review.md), [08-build-release.md §8](../../research/08-build-release.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`MagicFilter.resolve` walks its operation tuple through generic `resolve(value, initial_value)` calls (≈0.77 µs per
filter). D37 keeps magic-filter as an external dependency but compiles each `F` expression into a specialised Python
closure at snapshot compile (≈0.2 µs *est.*), with no API change. R10 warns that this reads magic-filter's internal
representation while D70 allows uncapped versions (3.x pins `magic-filter>=1.0.12,<1.1` in `pyproject.toml`; 4.0
keeps lower bounds only), so the compiler must fall back safely.

## Scope

**In:**
- Compiler (proposed `aiogram/utils/magic_filter_compile.py` or inside `aiogram/dispatcher/`) mapping a `MagicFilter`'s
  `_operations` to a closure. Supported subset, each with a matching unit test against `.resolve`:
  `GetAttributeOperation`, `GetItemOperation`, `CallOperation` (no-arg / constant args), `ComparatorOperation`
  (`==`, `!=`, `<`, `<=`, `>`, `>=`), `FunctionOperation` for `in_`, `contains`, `len`, `regexp`, `startswith`,
  `endswith`, `lower`/`upper`-style calls, `CombinationOperation` (`&`, `|`), `ImportantCombinationOperation`,
  `RCombinationOperation`, `SelectorOperation`, `CastOperation`, `ExtractOperation`, the inversion flag, and aiogram's
  `AsFilterResultOperation` (`.as_()`).
- **Fallback:** any operation class not in the supported set (by exact type, not `isinstance`, so a subclass
  falls back), any attribute access raising, or an unknown magic-filter major version → use `MagicFilter.resolve`
  unchanged. Compilation never changes results; it is only a speed path.
- Exception semantics identical to `.resolve` (magic-filter swallows `RejectOperations`; the compiled closure must too).
- Hooked into the E-07 compiled filter plan for `FilterObject.magic`.
- CI job (or I-05 matrix entry) running the agreement tests against the **newest** magic-filter release, plus the
  declared lower bound.

**Out:**
- Compiled rejectors and literal index (E-09 reads the compiled form's structure for `F.a.b == literal`).
- Upstreaming a compile API to magic-filter (possible later, 03 §6).

## Checklist

- [ ] Compiler for the supported subset with exact-type dispatch and fallback.
- [ ] Agreement test matrix: each supported op × representative events (text, captions, nested `None`, callbacks,
  missing attributes) asserts `compiled(event) == F.resolve(event)`, including truthiness and returned dicts.
- [ ] Property-style test generating random `F` chains from the supported subset with a seeded `random` generator
  (hypothesis is not a dependency; don't add one, AGENTS.md).
- [ ] Fallback test: a custom `BaseOperation` subclass and a subclassed `MagicFilter` resolve via `.resolve`.
- [ ] Newest-magic-filter CI job (coordinate with I-05).
- [ ] `pyproject.toml` lower bound only for `magic-filter` (D70) — confirm with I-07, which owns dependency bounds.
- [ ] Changelog fragment (`misc`/perf).

## Acceptance criteria

- Agreement matrix: 0 mismatches over ≥10 000 generated cases on both the lower-bound and newest magic-filter.
- Bench: `F.text == "x"` resolve ≤ 0.3 µs median on A-04 case `routing.20-ftext` (A-05 harness; vs ≈0.77 µs
  `.resolve`).
- Any unsupported operation path is covered by a test proving fallback.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Vendor magic-filter into aiogram | Keeps an external package users already import | D37 |
| Rust MagicFilter evaluator | ≤1–3 µs/update gain, not planned for 4.0 | 03 §6 |
| Upper-cap magic-filter to protect the compiler | Contradicts lower-bounds-only policy | D70 |

## Validation

```bash
make dev
uv run pytest tests -q
uv run --with 'magic-filter>=1.0.12' pytest tests -k magic -q     # newest
make lint
uv run mypy aiogram
uv run python -m benchmarks compare --base v4-baseline/3.x-optimised --head WORKTREE --cases routing.20-ftext
```

## Workflow notes

- E-09 needs the compiled representation to expose "path + comparator + literal" for rejectors; design the closure
  builder to return a small descriptor alongside the closure.

## Notes
