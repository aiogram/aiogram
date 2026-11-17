# C-05 — `errors.json` adapter

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-01](C-01-crate-xtask-ir-snapshot.md) |
| Blocks | [C-08](C-08-merge-cross-check.md), [C-12](C-12-enums-error-reason-emitter.md) |
| Gate-conditional | no |
| Decisions | D47, D118, PD-24 |
| Sources | [03-routing.md §5 D47](../../research/03-routing.md), [02-butcher.md §2, §5](../../research/02-butcher.md), [plans README PD-24](../README.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D47 adds `e.reason` (an `ErrorReason` `StrEnum`) to the unchanged 3.x exception classes. It is generated from
`errors.json`: 945 messages, 37 `%s`/`%d` templates, and MTProto codes where they exist. This task turns the file into
an IR error catalogue. Naming and emission happen in C-12.

## Scope

**In:** `crates/butcher/src/sources/errors.rs`, producing `ir.errors.json`. Each entry has the message text, HTTP/API
error code, MTProto code (if present), whether it is a template, its template placeholders (`%s`/`%d` in order, with a
type), and the methods it applies to (if the file lists them). Template messages are compiled to an anchored regex here,
so C-12 only emits.

**Out:** member naming, overlay name pins (PD-24) and the Python emitter (C-12); exception mapping in the session (D-02).

## Checklist

- [ ] Parse `errors.json` with `deny_unknown_fields`, warning (not failing) on new top-level keys, since the format is undocumented.
- [ ] Template detection and regex compilation, with one test per placeholder kind.
- [ ] Count assertion behind `BUTCHER_LIVE=1`: 945 messages, 37 templates.
- [ ] Fixture tests on a hand-written excerpt.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- Every template regex matches its own example rendering, and no exact message matches two templates (test over the live file, gated).
- Output is byte-identical across two runs.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| New exception classes per error | Breaks `except TelegramBadRequest` mental model; enum on `e.reason` instead | D47 |

## Validation

```bash
cargo clippy --all-targets -- -D warnings
cargo test -p butcher errors
BUTCHER_LIVE=1 cargo test -p butcher errors_counts -- --ignored
```

## Workflow notes

- If the OpenAPI host is unreachable, the previous snapshot's `ir.errors.json` is reused, and the manifest records that (C-08).

## Notes
