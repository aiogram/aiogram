# 3x-07 — Import time: drop the import-time `model_rebuild` loop

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-05](../A-contracts/A-05-bench-harness.md) |
| Blocks | [A-06](../A-contracts/A-06-record-3x-baselines.md) |
| Gate-conditional | no |
| Decisions | R27 (verify every forward ref and first-use concurrency, not only import timing) |
| Sources | [09 #5](../../research/09-3x-quick-wins.md), [01 §1](../../research/01-models.md), [01 §2](../../research/01-models.md), [codex-review R27](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`import aiogram.types` takes 1.46 s, and 920 ms of that is self-time in the loop at the end of
`aiogram/types/__init__.py`:

```python
for _entity_name in __all__:
    ...
    _entity.model_rebuild(_types_namespace=_types_namespace)
```

That loop builds the schema of all 665 classes eagerly, which defeats `defer_build=True` on `TelegramObject`
(`aiogram/types/base.py`). `TelegramMethod` (`aiogram/methods/base.py`) doesn't set `defer_build` at all. The
estimated gain is 1.4 s → ≈0.3 s.

The tail of `types/__init__.py` is hand-written: butcher only rewrites the import and `__all__` blocks. Check that
butcher preserves the change after `butcher apply all`.

## Scope

**In:**
- Remove the eager loop.
- Make every forward reference resolvable when pydantic builds a schema on first use. Types refer to each other
  through `TYPE_CHECKING`-only imports, so the names are missing from each module's globals; that is why the loop
  passes `_types_namespace`. Candidate mechanisms:
  - (a) inject the namespace lazily: a hook in `TelegramObject` (for example `__pydantic_init_subclass__`, or
    overriding the first-build path) calls `model_rebuild(_types_namespace=…)` for that class only on its first use;
  - (b) populate each type module's globals with the names it needs at the end of `types/__init__` (plain dict
    updates, no schema build);
  - (c) whatever pydantic ≥ 2.7 (the current floor) supports natively for parent namespaces.
- Add `defer_build=True` to `TelegramMethod`.

**Out:**
- Replacing the `TYPE_CHECKING` stubs with generated `.pyi` files: 4.0 (C-14).
- `unittest.mock.sentinel` import time: dropped 09 #15 (D120).

## Checklist

- [ ] Baseline with A-05 on `import.aiogram` (subprocess, cold, median of 7) and `update.realistic` first-decode
      latency (fresh process).
- [ ] Decide the mechanism (a/b/c) by prototype and measurement. Proposed default: (a) if it costs < 5 ms on first
      use per class, otherwise (b). Record the choice and the numbers in Notes.
- [ ] Remove the loop and add `defer_build` to `TelegramMethod`.
- [ ] Forward-reference test (fresh subprocess per check):
  - every name in `aiogram.types.__all__` and `aiogram.methods.__all__` can build its schema (`model_json_schema()`
    or validation of a minimal instance) with no "not fully defined" error;
  - generate the list, don't hand-write it.
- [ ] Concurrency test: 8 threads validate the same never-built type at the same moment (barrier). There are no
      errors and all results are equal. Run on 3.14t in CI if available; otherwise record that in Notes.
- [ ] Run `butcher apply all` and confirm the tail change survives (`git diff --exit-code`).
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.misc.rst`: "`import aiogram` is ≈N× faster", with the number from A-05.
- [ ] Migration registry: no entry.

## Acceptance criteria

- A-05 `import.aiogram` median ≤ 40% of the parent commit's.
- The generated forward-reference test passes for 100% of the exported types and methods.
- The concurrency test passes 50 runs in a row.
- The full suite passes.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep the eager rebuild | 920 ms of import self-time | 09 #5 |
| Generated `.pyi` stubs instead of `TYPE_CHECKING` blocks in 3.x | That is the 4.0 emitter (C-14); too large for a 3.x quick win | D16 |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run --extra cli butcher apply all && git diff --exit-code
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases import.aiogram
```

## Workflow notes

Part of the "optimised 3.x" baseline tag (A-06). Import time is not a B gate metric, but the README compares against
it. Parallel with everything except 3x-08, which also regenerates types; rebase whichever lands second.

## Notes
