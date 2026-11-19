# 3x-08 — Butcher: `Literal["x"]` tag fields; measure-or-drop the `RichTextUnion` field discriminator

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-04](../A-contracts/A-04-pinned-corpus.md) (corpus inputs `update.realistic`, `update.richtext`), [A-05](../A-contracts/A-05-bench-harness.md), [A-08](../A-contracts/A-08-model-oracle.md) (invariance check) |
| Blocks | [A-06](../A-contracts/A-06-record-3x-baselines.md) |
| Gate-conditional | no |
| Decisions | PD-28 (#8 measured or dropped; behaviour-changing → minor), AGENTS.md codegen rule |
| Sources | [09 #7, #8](../../research/09-3x-quick-wins.md), [01 §1–2](../../research/01-models.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Tag fields are generated as `Literal[Enum.MEMBER]`, for example `ChatMemberOwner.status:
Literal[ChatMemberStatus.CREATOR] = ChatMemberStatus.CREATOR`. pydantic validates them with a Python callback, about
80 per realistic update. `Literal["creator"]` validates in Rust. That is part of the ≈30 µs of Python work inside an
84 µs parse (01 §1).

09 #8 proposes a field discriminator for `RichTextUnion`. Its premise is doubtful: the union has `str` and
`list["RichTextUnion"]` members (`aiogram/types/rich_text_union.py`), so a plain `Field(discriminator="type")` can't
cover it. That is why #1925 introduced the callable `_rich_text_union_tag`. PD-28: measure it or drop it.

## Scope

**In:**
- Change generation so tag fields are `Literal["value"]` with the plain string default, through the butcher path
  (AGENTS.md). The emitter for these annotations lives in the butcher tool (installed through the `cli` extra,
  `aiogram-cli`), not in `.butcher/templates` (those are docs-only `.rst` templates). Locate the emitter first.
- `RichTextUnion` (#8): prototype a nested form, for example `str | list[...] | Annotated[Union[RichText…],
  Field(discriminator="type")]`, and measure it on `update.richtext`. Adopt it only if it gains ≥ 10% on that input
  and validates identically; otherwise drop it and record the numbers.

**Out:**
- `Unknown` fallback variants: [3x-18](3x-18-unknown-union-fallback.md).
- 4.0 enum emission: C-12.

## Checklist

- [ ] Locate the `Literal[...]` emitter (`uv sync --extra cli`, then find it in the installed butcher package).
- [ ] Decide where the change lives. Proposed default:
  - a per-run option or overlay key in `.butcher`, if the tool supports one;
  - otherwise a change and release of the butcher tool first, with the `cli` extra's lower bound raised.

  Record the choice in Notes and flag it to the owner if a tool release is needed.
- [ ] Baseline with A-05 on `update.realistic` and `response.getUpdates.100` decode.
- [ ] Regenerate with `butcher parse` / `refresh` / `apply all`. Commit the config and the generated output together.
- [ ] Typing check. A small `mypy` snippet in `tests/` (or a `pytest-mypy` case) shows what happens to
      `m.status == ChatMemberStatus.CREATOR` and to `match` on the status. Record whether users see new mypy
      errors; that decides the changelog wording.
- [ ] Runtime equality: `ChatMemberOwner(...).status == ChatMemberStatus.CREATOR` stays true, because the enums are
      `str` subclasses. Add the test.
- [ ] Model oracle (A-08), parent vs this commit: every case is invariant.
- [ ] #8 prototype, measurement and the adopt/drop decision, recorded in Notes.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.misc.rst` (or `.feature.rst` if typing changes for users), with the typing
      note. Ship in a 3.x **minor** (PD-28).
- [ ] Migration registry: no entry. This is a 3.x typing change; 4.0's enum model is C-12.

## Acceptance criteria

- A-05 `compare` on `update.realistic`: decode median ≥ 10% faster than the parent commit. If it is less, record it
  and still ship only if the owner agrees.
- A-08 model oracle: zero mismatches.
- `butcher apply all` is reproducible: `git diff --exit-code` after regenerating.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Hand-edit the generated `aiogram/types/*.py` | Regeneration reverts it | AGENTS.md |
| Plain field discriminator for `RichTextUnion` | The union has `str` / `list` members; #1925 needed a callable | PD-28 |

## Validation

```bash
uv run --extra cli butcher parse && uv run --extra cli butcher refresh && uv run --extra cli butcher apply all
git diff --exit-code
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases update.realistic,update.richtext,response.getUpdates.100
uv run python -m differential run --kind model --left git:HEAD~1 --right git:HEAD
```

## Workflow notes

- C-11 (`import-legacy`) must import the `.butcher` state after this lands.
- Part of the "optimised 3.x" parse baseline (A-06).

## Notes
