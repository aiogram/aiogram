# C-21 — Generated-tests emitter

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-18](C-18-rust-type-emitter.md), [C-19](C-19-rust-forward-compat-emitter.md), [C-20](C-20-rust-methods-shortcuts-emitter.md), [A-04](../A-contracts/A-04-pinned-corpus.md) |
| Blocks | [C-25](C-25-historical-scenario-tests.md), [D-07](../D-client/D-07-rust-encoder-json.md) |
| Gate-conditional | yes |
| Decisions | D10, D100, D72, R26, 19 §8 (text_signature, strict corpus) |
| Sources | [02-butcher.md §5 (Tests)](../../research/02-butcher.md), [10-forward-compatibility.md §3 (Visibility and strictness)](../../research/10-forward-compatibility.md), [19 §2 R26, §8](../../research/19-review-resolutions.md), [08-build-release.md §5](../../research/08-build-release.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Every generated surface needs a test that fails when the generator breaks it. 02 §5 lists per-type JSON round-trip,
per-method encode, per-shortcut fill and deprecation-warning tests. 19 §8 adds `inspect.signature` on every generated
signature and **strict** mode for known-schema corpus tests. Expected values must not all come from the same IR the
code was generated from (R26), so the emitter is paired with hand-curated wire fixtures.

## Scope

**In:** `crates/butcher/src/emit/tests.rs` → `tests/test_generated/` (pytest, regenerated whole):
- per type: `from_json(fixture).to_json()` round-trip on a minimal valid instance synthesised from the IR, **plus** every
  hand-curated wire fixture under `tests/data/wire/` that names the type (fixtures are hand-written, R26);
- per method: encode of a minimal instance via the D-07 encoder entry point; the JSON or multipart shape is asserted on
  wire names and `Default` omission;
- per shortcut: the filled params equal the DSL paths evaluated on a fixture object (C-07 table); guards raise;
- per ledger entry (fixture ledger in tests): `AiogramApiDeprecationWarning` on set and read;
- per generated signature: `inspect.signature(...)` succeeds and is keyword-only (19 §8);
- the strict corpus: A-04's recorded update corpus decoded with `DecodePolicy("strict")`; any `Unknown` or decode error fails (10 §3);
- the lenient counterpart: a test with injected unknown tags and update types in **lenient** mode (19 §8: the
  forward-compat feature itself needs explicit lenient tests).

**Out:** differential harness cases (D-15, A-07); historical diff scenarios (C-25).

## Checklist

- [ ] Test-file templates and the minimal-instance synthesiser from the IR.
- [ ] `tests/data/wire/` fixture loader (fixtures are hand-written or redacted recordings with provenance, R26).
- [ ] Strict corpus test on A-04's corpus; lenient forward-compat test.
- [ ] Coverage: the generated tests bring generated Python glue (`_bot_methods.py`, `_router_observers.py`, utils mixins) to 100%.
- [ ] Poison control: a deliberately corrupted emitter (fixture flag) must make the generated tests fail (R26).
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- `uv run pytest tests/test_generated` passes on a dev build, and the poison-control run fails with at least one failure per category.
- The strict corpus over A-04's pinned corpus reports 0 `Unknown` and 0 decode errors.
- The generated test files are byte-identical across two emits.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| IR-only expected values | Can't catch a wrong mapping | R26 |
| Lenient corpus tests | Hides butcher misses | 10 §3, 19 §8 |

## Validation

```bash
cargo xtask butcher emit && maturin develop --release
uv run pytest tests/test_generated
uv run pytest tests
cargo xtask butcher check
```

## Workflow notes

- A-04 provides the corpus, and D-07's encoder entry point is needed for the encode tests. C-25 builds on the same fixtures.

## Notes
