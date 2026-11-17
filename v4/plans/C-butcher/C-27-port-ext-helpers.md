# C-27 — Port the remaining hand-written type helpers to `*_ext.rs`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [B-10](../B-spike/B-10-ext-helpers-stub-workflow.md), [C-18](C-18-rust-type-emitter.md), [D-17](../D-client/D-17-rust-entity-rendering-kernel.md), [B-13](../B-spike/B-13-gate-run-and-decision.md) |
| Blocks | [I-04](../I-distribution/I-04-installed-wheel-typing-stubtest.md), [J-01](../J-ga/J-01-feature-inventory-audit.md) |
| Gate-conditional | yes |
| Decisions | D11, PD-16, PD-15, D100 (not applied, hand-written APIs keep their signatures), D109 |
| Sources | [02-butcher.md §5.1](../../research/02-butcher.md), [01-models.md §3.4, §5 step 3](../../research/01-models.md), [06-utils.md §1–2](../../research/06-utils.md), [13-aiogram-rust-review.md §4, B10](../../research/13-aiogram-rust-review.md), [plans README PD-15, PD-16](../README.md), `aiogram/types/{user,chat,contact,message,message_entity,inaccessible_message}.py` (3.x) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

02 §5.1 counts 26 hand-written methods in 12 type classes on 3.x. D11 moves them to Rust `*_ext.rs` impl blocks with
`.pyi` fragments; there is no Python facade. B-10 ports only 2–3 to validate the workflow (01 §5 step 3:
`User.mention_html`, `Message.html_text`). PD-16 assigns the rest here.

A scan of dev-3.x (methods in `aiogram/types/*.py` that are not generated shortcuts) splits the 26 as follows:

| Helper | 4.0 home |
|---|---|
| `User.full_name`, `User.url`, `User.mention_html`, `User.mention_markdown` | `user_ext.rs` (this task, minus B-10's `mention_html`) |
| `Chat.full_name`, `Chat.shifted_id` | `chat_ext.rs` |
| `Contact.full_name` | `contact_ext.rs` |
| `InaccessibleMessage.as_reply_parameters` | `inaccessible_message_ext.rs` |
| `Message.as_reply_parameters`, `Message.as_ephemeral_message_parameters`, `Message.get_url` | `message_ext.rs` |
| `Message.html_text`, `Message.md_text`, `Message._unparse_entities`, `MessageEntity.extract_from` | `message_ext.rs` / `message_entity_ext.rs` on the D-17 entity kernel (PD-15), minus B-10's `html_text` |
| `Update.__hash__`, `Update.event_type`, `Update.event` | **generated** (C-19), not ported |
| `Message.send_copy` | **generated** (C-20) |
| `Message.content_type` | **removed** (11 §1) |
| `InputFile.read` and the `BufferedInputFile.from_file`/`read`, `FSInputFile.read`, `URLInputFile.read` family | stays plain Python (02 §5.1) |
| `Downloadable.file_id` | a `typing.Protocol`; stays Python |

## Scope

**In:** the hand-written Rust helpers above (16 methods in 7 classes, minus whatever B-10 already ported), each with a
sibling `<type>_ext.pyi` fragment, using the B-10 workflow (`multiple-pymethods`, fragment merge by C-14). Signatures
stay exactly as in 3.x, including positional parameters such as `get_url(force_private=False, include_thread_id=False)`.
D100 covers generated signatures only (01 §3.4). **Parity tests** are derived from today's Python behaviour, e.g.
`mention_html` escaping equals `html.escape`, and `html_text`/`md_text` equal 3.x on A-04's formatting corpus.

**Out:** the workflow itself (B-10); the entity kernel (D-17); the formatting API (G-08); `InputFile` (D-04).

## Checklist

- [ ] Port each helper listed for this task; register its names in the ext fragment (C-09 reserved-name derivation picks them up).
- [ ] Parity tests in `tests/test_api/test_types/` against recorded 3.x outputs (generated in the pinned 3.x venv, PD-12).
- [ ] `html_text` / `md_text` / `extract_from` on D-17's kernel, with a UTF-16 surrogate and nested-entity corpus.
- [ ] Remove the Python implementations from the 4.x tree once the Rust ones pass (respecting PD-03 staging until B-13 is a go).
- [ ] Migration-registry entry (PD-13): none expected (same names and signatures). If a behaviour difference is found, add a `removal-4.0` or approved-difference entry and record it in Notes.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- Every helper in this task's rows exists on the Rust class and appears in the merged stub (`stubtest` clean for these names).
- The parity tests pass with 0 differences on recorded 3.x outputs (approved differences, if any, carry a decision id, R26).
- `Message.html_text` on A-04's pinned 230-char / 6-entity input is at least as fast as the 3.x 22 µs baseline (06 §1).
- A name collision between an ext helper and a generated member fails compilation (multiple-pymethods) **and** C-09's collision check, before compile.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Python helpers attached at import (aiogram_rust: 4 974 lines) | One language per type, native speed | D11, 13 §4 |
| Making the helpers keyword-only | D100 covers generated signatures; hand-written APIs keep theirs | 01 §3.4 |
| Leaving the port unowned | Gap found in planning | PD-16 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test -p aiogram-core
make dev
uv run pytest tests/test_api/test_types
uv run mypy aiogram
cargo xtask butcher check
```

## Workflow notes

- Needs B-10's workflow and C-18's generated classes. `html_text`/`md_text` need D-17. C-20's shortcuts call `as_reply_parameters()` and `as_ephemeral_message_parameters()` as DSL helpers. C-20 can land with the DSL resolving those names from the fragments, and the runtime calls succeed once this task lands.

## Notes
