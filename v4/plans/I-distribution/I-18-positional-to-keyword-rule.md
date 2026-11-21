# I-18 — Codemod rule: positional → keyword API calls (D100)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-15](I-15-receiver-inference.md), [C-26](../C-butcher/C-26-removal-inventory-signature-table.md), [G-11](../G-features/G-11-generated-utils-signatures.md) |
| Blocks | [I-20](I-20-examples-port-smoke.md), [I-22](I-22-migration-rehearsal.md), [I-23](I-23-beta-pre-release.md) |
| Gate-conditional | no |
| Decisions | D100, D101, PD-02, PD-23, R28 |
| Sources | [16-support-policy.md §2.2–2.3](../../research/16-support-policy.md), [01-models.md §3.4](../../research/01-models.md), [README breaking change 21](../../research/README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D100 (kept by the owner, PD-02) makes every generated signature keyword-only: `Bot` methods, all shortcuts and the
constructors. `message.answer("hi")` and `bot.send_message(1, "hi")` raise `TypeError` in 4.0. Almost every 3.x bot
contains these calls, which makes this the highest-volume item in the migration.

The codemod rewrites positional calls to keyword form using the **3.x signature order** (C-26 table). The checker
reports the rest (D101). Coverage depends on I-15's inference, including the observer-decorator source.

## Scope

**In:**
- **Targets.**
  - `bot.<method>(...)` where the receiver infers to `Bot`;
  - `<obj>.<shortcut>(...)` where the receiver infers to a type that has that shortcut in the C-26 3.x table;
  - generated type and method constructors called positionally (3.x pydantic models were already keyword-only, so
    expect near zero; report if seen).
- **Rewrite.** Map each positional argument to the 3.x parameter name at that position. Keep keyword arguments as they
  are. A **positional parameter removed in 4.0** (ledger reset, e.g. `reply_to_message_id`) is renamed to its 3.x name
  and the I-16 ledger rule then reports it, so this rule never drops an argument.
- **Splats.** `*args` / `**kwargs` call sites are reported and never rewritten.
- **Confidence.**
  - Receiver at high confidence (annotation / `isinstance`): definite fix.
  - Medium (observer decorator, attribute chain): **heuristic** fix, applied only with `--heuristic`.
  - Unresolved receiver whose method name exists **only** as an aiogram API name (from the C-26 name set, e.g.
    `answer_photo`, `send_message`, `edit_text`): heuristic report with low confidence.
  - Other unresolved receivers: nothing.
- **Shortcut quirk.** Shortcuts pre-fill parameters (`chat_id` from `self.chat.id`). The 3.x shortcut signature (not
  the method's) defines the order, so the C-26 table must carry shortcut signatures separately.

**Out:**
- Inference (I-15).
- Removed-field reporting (I-16).
- Hand-written non-generated APIs with their own signatures (`bot.call(name, params)`, D96): untouched.

## Checklist

- [ ] `rules/keyword_only.py` using `infer()` and the C-26 signature table (methods and shortcuts separately).
- [ ] Golden tests:
      - `bot.send_message(1, "hi")`;
      - `message.answer("hi")` (annotated → definite; decorated but unannotated → heuristic);
      - `callback.message.answer("x")` (attribute chain → heuristic);
      - `await message.reply_photo(photo, caption)`;
      - mixed positional plus keyword arguments;
      - `*args` (report);
      - an unresolved receiver with a unique API name (low-confidence report);
      - an unresolved receiver with a non-unique name (`.answer` on an unknown object → no finding).
- [ ] Measure the definite / heuristic / unfixed split on the 3.x `examples/` and record it in Notes (input to I-22).
- [ ] Registry id for breaking change 21 (A-11 seed), with codemod coverage "partial".
- [ ] Tests (100% coverage of the rule module).
- [ ] Changelog fragment `CHANGES/<id>.feature.rst` (migrate rewrites positional API calls).

## Acceptance criteria

- Golden tests pass, and every `after` compiles.
- On 3.x `examples/`, `check` finds 100% of positional `Bot` / shortcut calls that a manual grep lists. The grep list is
  committed as the test oracle.
- `fix` (default, definite only) never rewrites a medium-confidence receiver. `fix --heuristic` does.
- After `fix --heuristic`, running the ported examples (I-20) raises no `TypeError: takes 0 positional arguments`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keeping positional arguments for the first required parameter | Keyword-only kept as decided | D100, PD-02 |
| Rewriting unresolved receivers by method name alone, by default | False positives on non-aiogram objects; low-confidence report only | R28 |
| `**extra` in stubs so type checkers accept unknown kwargs | Runtime-only | PD-23 |

## Validation

```bash
make dev
uv sync --extra migrate
uv run pytest tests/test_migrate -q
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: I-15 (`infer()`), C-26 (3.x method and shortcut signatures).
- Outputs: the largest share of I-22's rehearsal coverage.
- Runs in parallel with I-16, I-17 and I-19.

## Notes

(empty)
