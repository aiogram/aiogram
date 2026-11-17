# E-09 — Routing keys and compiled rejectors (prefilter, literal and command index)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-02](E-02-dispatch-table-executor.md), [E-08](E-08-magic-filter-compile.md), [B-05](../B-spike/B-05-views-cache-gc-routing-keys.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [C-16](../C-butcher/C-16-router-observers-update-tables.md), [C-19](../C-butcher/C-19-rust-forward-compat-emitter.md) |
| Blocks | [E-21](E-21-e-exit-gate.md), [F-15](../F-fsm/F-15-statefilter-state-index.md), [G-12](../G-features/G-12-commands-from-handlers.md), [I-19](../I-distribution/I-19-heuristic-behaviour-rules.md) |
| Gate-conditional | **yes** — consumes the Rust `update.routing_keys()` from B-05 (D26 / 13 B14); re-validate after B-13 |
| Decisions | D26, D111, PD-19, 13 B13, 13 B14, README breaking change 13 |
| Sources | [03-routing.md §3](../../research/03-routing.md), [13-aiogram-rust-review.md §1, §3 B13/B14, §4](../../research/13-aiogram-rust-review.md), [19 D111](../../research/19-review-resolutions.md), [codex-review R10](../../research/codex-review.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

With native objects every attribute read crosses into Rust; aiogram_rust's Python router over native types was 13%
slower than 3.x until a prefilter was added (13 §1: 100 Commands 280 → 18.3 µs). 03 §3 adopts two things:
`update.routing_keys()` — event type, parsed command, text, callback data, chat type and content kind in **one Rust call**,
cached per update (B14) — and **compiled rejectors** that skip a candidate as soon as a compiled filter is certainly
false, even when user filters come before it (B13, breaking change 13). The literal index generalises the command
index. This plan replaces E-02's Python shim with the B-05 call and adds rejectors to the compiled plan.

## Scope

**In:**
- Swap the E-02 `routing_keys` shim for `update.routing_keys()` (B-05). Keep the shim behind a test fixture so
  agreement tests can compare both.
- **Command parsing once per update**, cached in the routing keys / data: split rule identical to Python `str.split`
  (3.x `Command` uses `text.split(maxsplit=1)` then `partition("@")`), including U+001C–U+001F whitespace; prefix is the
  first character.
- **Rejectors** compiled per candidate from:
  - `Command` with plain-string commands, default `prefix="/"`, no `magic`, `ignore_case=False` — rejects on **command
    name only**; mention checks (`bot.me()`, secondary usernames from #1984) stay in the real filter;
  - truthy `F.a.b` (path present and truthy);
  - `F.a.b == literal` (str/int/bool/None/enum literals).
  Regex commands, `ignore_case`, custom prefixes, `Command` subclasses and other filters stay in the normal path.
- **Literal index** `{(path, literal): positions}` per `EventPlan`; one attribute read per distinct path per update,
  not per handler; paths covered by routing keys read from them.
- **Skip rule:** a candidate is skipped as soon as any compiled rejector is certainly false; its other filters (also
  those registered before it) don't run. PD-19: a router frame is entered only if a candidate in its subtree survives.
- **Agreement test:** over a matrix of filters × events, whenever a rejector rejects, the real filter returns falsy
  (never the reverse claim).
- Docs: "filters must not rely on running for handlers that can't match" (breaking change 13).

**Out:**
- The Rust `routing_keys()` implementation (B-05); the Rust routing content-kind table (C-19, from the C-06 overlay
  kind 14).
- Scene state index (F-15, a frame-skip hook under the same D111 rule).

## Checklist

- [ ] Replace the shim; routing-keys object cached once per update.
- [ ] Command parse-once with the exact `str.split` rule; tests for U+001C–U+001F, `\xa0`, tabs, `@mention`,
  `/cmd@bot args`, empty text, caption commands (3.x `Command.__call__` reads `message.text or message.caption` and
  `Command.extract_command` does `text.split(maxsplit=1)` then `full_command[1:].partition("@")`; match both).
- [ ] Rejector compilation for the three forms; literal index.
- [ ] Executor skip rule + PD-19 frame skip.
- [ ] Decide how rejectors treat a registered subclass that overrides a routed property such as `text` (R10;
  proposed default: if any subclass is registered (`aiogram.types.register`, B-08) for the event's type, disable
  rejectors for that event type in the snapshot) — record in Notes and flag to owner.
- [ ] Document that rejectors read keys computed at the routing stage (E-02 decision), so a router-level outer
  middleware that replaces the event does not change rejector decisions (D111).
- [ ] Agreement matrix and difference-manifest entries (A-07) for breaking change 13 with narrow assertions.
- [ ] Migration-registry entry (PD-13) for breaking change 13 (manual checklist item: side-effecting filters) and a
  changelog fragment.
- [ ] Tests: 100% coverage of compiler and index.

## Acceptance criteria

- Agreement matrix: 0 cases where a rejector rejects and the real filter passes.
- A-10 differential: every difference is covered by the D111 / breaking-13 manifest entries.
- Bench (A-05 scenarios, compared with the A-06 optimised-3.x baseline, Linux + macOS):
  - `routing.52-handlers` (03 §2) worst case (mid/last/unhandled) **≤ 90 µs**, fixed overhead **≤ 15 µs**;
  - `routing.100-commands` (100 plain `Command` handlers), unmatched command: **≤ 25 µs**;
  - end-to-end dispatch on the B-12 realistic router: **no slower than optimised 3.x** (D26 gate condition).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Skip a candidate only when the rejector is its first filter | Most of the win comes from skipping regardless of order; accepted as documented break | 13 §4, breaking 13 |
| One FFI getattr per handler | 13% slower than 3.x in aiogram_rust | D26, B14 |
| Rust `split_whitespace` for commands | Differs from Python `str.split` for U+001C–U+001F | 13 §4 |
| Native (Rust) prefilter | Built in Python on the snapshot; sound skip rule is enough | B13 |

## Validation

```bash
make dev
cargo test
uv run pytest tests -q
uv run python -m differential run --kind routing --left pypi:aiogram==<A-10 pinned 3.x version> --right path:.
make lint
uv run mypy aiogram
uv run python -m benchmarks compare --base v4-baseline/3.x-optimised --head WORKTREE --cases routing.52-handlers,routing.100-commands
```

## Workflow notes

- Until B-05 lands, work can start against the shim; the plan is done only when the Rust call is wired and the
  benchmarks above are met.
- If B-13 is a no-go this plan becomes `blocked`; the rejector design itself is model-agnostic and can be re-planned
  over whatever model layer replaces it.

## Notes
