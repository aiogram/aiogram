# C-07 — Fill-DSL for shortcuts

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-06](C-06-overlay-schema-loader.md) |
| Blocks | [C-11](C-11-import-legacy.md), [C-20](C-20-rust-methods-shortcuts-emitter.md) |
| Gate-conditional | no |
| Decisions | D11, D100 |
| Sources | [02-butcher.md §3 item 5, §6](../../research/02-butcher.md), [01-models.md §3.4](../../research/01-models.md), `.butcher/types/*/aliases.yml` (3.x) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Shortcuts (`Message.answer`, `CallbackQuery.answer`, …) are generated in Rust from the overlay (D11). The legacy
overlay stores Python `fill` expressions and `code` guard snippets. The research never specified the DSL grammar
(02 §3 gives only two examples). A survey of all 13 `aliases.yml` files (189 shortcuts) found a small closed set of
shapes:

| Count | Legacy expression | Shape |
|---|---|---|
| 130 | `self.chat.id` | path |
| 45 | `self.business_connection_id` | path |
| 38 | `self.message_thread_id if self.is_topic_message else None` | path `when` path |
| 38 | `self.as_reply_parameters()` | zero-arg helper call |
| 34 | `self.direct_messages_topic.topic_id if self.direct_messages_topic else None` | optional-chained path |
| 13 | `self.as_ephemeral_message_parameters()` | zero-arg helper call |
| rest | `self.id`, `self.user_chat_id`, `self.receiver_user.id`, … , one literal `None` | path / literal |

Guards (97 `code` entries) are all `assert <path> is not None, "<msg>"` or `assert <path> is None, "<msg>"`.

## Scope

**In:** `crates/butcher/src/dsl.rs`: grammar, parser, and typed resolution against the merged IR.

Proposed grammar (see the Decide item):
```toml
[answer]
method = "sendMessage"
require = [{ path = "self.chat", message = "This method can be used only if chat is present in the message." }]
forbid  = []                                  # `assert X is None` guards
ignore  = []                                  # params never forwarded
[answer.fill]
chat_id = "self.chat.id"
message_thread_id = { expr = "self.message_thread_id", when = "self.is_topic_message" }
direct_messages_topic_id = "self.direct_messages_topic?.topic_id"   # optional chaining → None
reply_parameters = "self.as_reply_parameters()"                     # zero-arg helper (generated or *_ext)
```
- `expr` := `path` | `path?.path` | `helper()` | `None` | literal; `path` := `self(.ident)+`.
- `when` := `path` (truthiness). A false `when` means the argument is omitted (the method default applies), matching
  `… else None` today.
- Typed resolution: every path segment must exist on the IR type (after D109 renames). A helper must be either a
  generated member or declared in a `<type>_ext.pyi` fragment list. The value type must be assignable to the target
  param type. A fill key must be a declared param of the target method; an undeclared key is an error, which fixes the
  "undeclared field leaks into the request" note in `Message/aliases.yml`.
- `handwritten = true` marks a shortcut that the DSL can't express; it lives in `<type>_ext.rs` (D11).
- Output: a resolved shortcut table in the IR, consumed by C-14 (stubs) and C-20 (Rust).

**Out:** Rust code generation for shortcuts (C-20), translating the legacy YAML (C-11).

## Checklist

- [ ] **Decide the fill-DSL grammar** (proposed default: the grammar above, i.e. paths, `?.` optional chaining,
  `when`, zero-arg helpers, literals, `require`/`forbid` guards; no arbitrary expressions). Record it in Notes and flag
  it to the owner before C-11 starts.
- [ ] Parser with spans; errors point to the TOML file, key and column.
- [ ] Typed resolver against the IR (paths, helpers, param existence, assignability).
- [ ] **Decide the guard exception type** (proposed default: keep `AssertionError` with the legacy message, matching 3.x,
  but raised explicitly so `python -O` doesn't strip it). Record it in Notes with the grammar decision.
- [ ] A fixture test per expression shape in the survey table.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- A fixture corpus of the legacy shortcut `fill` expression shapes (taken from `.butcher/` on dev-3.x) parses and resolves with 0 failures. The end-to-end "0 `handwritten` caused by DSL gaps" import count is C-11's criterion.
- A fill key that is not a param of the target method fails `build` with the key and method named.
- A path through a field removed upstream fails with the path and the ledger hint.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep Python expressions | Not checkable, needs a Python evaluator in Rust; drifts | 02 §3 |
| A Python facade per type for shortcuts | One class per type, decoder instantiates it directly | D11 |
| Positional shortcut params | Every generated signature is keyword-only | D100, PD-02 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test -p butcher dsl
```

## Workflow notes

- C-11 translates the legacy expressions into this grammar. C-20 consumes the resolved table.

## Notes
