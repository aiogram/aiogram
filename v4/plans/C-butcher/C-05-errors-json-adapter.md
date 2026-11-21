# C-05 — `errors.json` adapter

| Field | Value |
|---|---|
| Status | `done` |
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
`errors.json`: 962 messages, 38 `%s`/`%d` templates, and MTProto codes where they exist. This task turns the file into
an IR error catalogue. Naming and emission happen in C-12.

## Scope

**In:** `crates/butcher/src/sources/errors.rs`, producing `ir.errors.json`. Each entry has the message text, HTTP/API
error code, MTProto code (if present), whether it is a template, its template placeholders (`%s`/`%d` in order, with a
type), and the methods it applies to (if the file lists them). Template messages are compiled to an anchored regex here,
so C-12 only emits.

**Out:** member naming, overlay name pins (PD-24) and the Python emitter (C-12); exception mapping in the session (D-02).

## Checklist

- [x] Parse `errors.json` with `deny_unknown_fields`, warning (not failing) on new top-level keys, since the format is undocumented.
- [x] Template detection and regex compilation, with one test per placeholder kind.
- [x] Count assertion behind `BUTCHER_LIVE=1`: 962 messages, 38 templates (the live file of 2026-11-21; the first draft said 945 / 37).
- [x] Fixture tests on a hand-written excerpt.
- [x] Tests (100% coverage of new code)

## Acceptance criteria

- Every template regex matches its own example rendering (test over the live file, gated).
- Specificity rule: a message is looked up exactly first, then among the templates that match it the one with the longest
  literal (message length minus placeholders) wins, and that winner is unique. Templates overlap (`entity %s` also matches
  `entity begins after ... %d`), so "no message matches two templates" does not hold; the live test checks the rule instead.
- Output is byte-identical across two runs.

## Output shape (`ir.errors.json`, read by C-08 and C-12)

An `Ir` with `header` (`api_version` = the file's `version`, `sources: ["errors"]`, `html_only: false`) and `errors` only,
ordered by HTTP code, then message (the order of the sorted source objects). Entry: `code`, `message` (with the
`Bad Request: ` prefix), `mtproto` (only when the file gives exactly one code), `template`, `methods`. A template has
`placeholders` (`s` / `d`, in order) and an anchored `regex` with one capture group per placeholder.

- Regex dialect is the subset Python `re` and Rust `regex` share: `^...$`, `%s` is `(.*?)`, `%d` is `(-?\d+)`; use a
  full match. `%s` can render empty (`too big%s;`), which `(.+)` would reject.
- Consumers (C-12) look up the exact message first, then the matching template with the longest `literal_len`
  (`butcher::sources::errors::literal_len`).
- `mtproto_descriptions` and `parameters` (`retry_after`, `migrate_to_chat_id`) are not carried: the IR has no field for them.
- A new top-level key in the source is a warning (returned in `Parsed::warnings`); a malformed `errors` section is an error.
- `regex` is a dev-dependency of `butcher` only; the adapter emits the string and never compiles it.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| New exception classes per error | Breaks `except TelegramBadRequest` mental model; enum on `e.reason` instead | D47 |
| `mtproto: Vec<String>` in the IR, or the first code, for the 4 messages with several codes | The IR holds one code and PD-24 pins member names for good, so an arbitrary pick is worse than none: `mtproto` stays unset for them | C-05 |
| A `priority` field, or a `%s` regex that cannot overlap (`[^ ]+`) | The order is derivable from the literal length, and real values contain spaces (`URL '%s' is invalid: %s`) | C-05 |
| `\A...\z` anchors, named groups, `(.+)` for `%s` | Not shared by Python `re` (before 3.14) and Rust `regex`, or breaks on an empty `%s` | C-05 |

## Validation

```bash
cargo clippy --all-targets -- -D warnings
cargo test -p butcher errors
BUTCHER_LIVE=1 cargo test -p butcher errors_counts -- --ignored
```

## Workflow notes

- If the OpenAPI host is unreachable, the previous snapshot's `ir.errors.json` is reused, and the manifest records that (C-08).

## Notes
