# H-16 — Fake fidelity: modelled vs synthesised, trace replay, difference manifests

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-02](H-02-token-redaction-filter.md), [H-12](H-12-toolkit-model-api-migration.md), [A-04](../A-contracts/A-04-pinned-corpus.md), [A-07](../A-contracts/A-07-differential-framework.md), [D-15](../D-client/D-15-request-response-differential-cases.md) |
| Blocks | [H-20](H-20-integration-layer-exit-gate.md) |
| Gate-conditional | yes |
| Decisions | R26, D52, 13 B8 |
| Sources | [14-testing.md §3 "Fidelity", "Difference manifests"](../../research/14-testing.md), [19 R26](../../research/19-review-resolutions.md), [08-build-release.md §5 differential harnesses](../../research/08-build-release.md), [13-aiogram-rust-review.md B8](../../research/13-aiogram-rust-review.md), [codex-review.md R26](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

R26 makes three points:
- the fake is not an independent oracle of Telegram semantics;
- deriving both expected and actual values from the same IR can hide a wrong mapping;
- a synthetic result must never be mistaken for server behaviour.

So:
- the fake marks **modelled vs synthesised** methods visibly;
- recorded real-API traces and hand-curated wire fixtures (redacted, with provenance) are replayed against the
  fake's modelled methods;
- each case is classed by a **difference manifest**.

## Scope

**In:**
- Every recorded call (`aiogram/test/calls.py`) carries `source`: `"modelled"`, `"synthesized"` or `"override"`.
  - `pytest_assertrepr_compare` and `env` call-log reprs show it.
  - `env.synthesized_calls()` lists the calls whose results were synthesised, so a test can assert on it.
- Fidelity harness on A-07's differential framework:
  - Inputs: recorded `(method, params, response JSON)` traces and hand-curated wire fixtures.
  - Each case: run the method through the fake against a blueprint reconstructed from the trace's preconditions,
    then compare the fake's result with the recorded response after normalisation (ids, dates, file ids).
  - Normalisation rules are listed in the manifest, not in code comments.
- **Difference manifest** (R26), a data file next to the fixtures. Each case is one of:
  - `invariant`;
  - `approved-difference`, with a decision id and a narrow assertion of what differs;
  - `newly-supported`.

  No blanket exclusions.
- **Poison control** (13 B8): a test variant corrupts one modelled method's output. The harness must report that
  case as a mismatch, or the harness counts as broken.
- Recorded traces are redacted with the H-02 pattern before they are committed. Each file has a provenance header:
  date, Bot API version, aiogram commit, recorder.

**Out:**
- Codec fidelity (D-15 covers request/response encoding; D52).
- Recording infrastructure for production bots (out of scope). A maintainer records a seed set with a test bot.

## Checklist

- [ ] `source` on call records, the repr and `synthesized_calls()`.
- [ ] Harness, manifest schema (reuse A-07's manifest format if it has one) and the poison-control test.
- [ ] Seed fixtures: at least 20 modelled methods covering send/edit/delete, chat-member and callback flows. Taken
      from A-04's corpus where it holds request/response pairs; otherwise recorded by a maintainer (redacted,
      provenance).
- [ ] CI: harness runs in the normal `pytest` job (offline, fixtures committed).
- [ ] Docs (`testing.rst` "Fidelity" section): what modelled and synthesised mean, and how to check which you got.
- [ ] Changelog fragment (new visible call-record field).

## Acceptance criteria

- Every seed case is classed in the manifest, and the harness passes.
- The poison-control variant fails with a mismatch naming the corrupted method.
- A test that calls a method without a fake model sees `source == "synthesized"` in the call log and in the
  assertion repr.
- No committed fixture contains a token-shaped string. A test runs the H-02 pattern over the fixture directory.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Snapshot exclusions for 4.0 differences | Hide regressions; each difference needs a decision id and a narrow assertion | R26 |
| IR-derived expectations only | Same source on both sides can't catch a wrong mapping | R26 |
| Hiding synthesis from users | A synthetic success could be mistaken for server behaviour | R26 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Gate-conditional through H-12 (Rust-native types).
- Inputs:
  - A-07: differential framework;
  - A-04: corpus;
  - D-15: request/response cases and their manifest conventions;
  - H-02: redaction pattern.
- Output: the fidelity suite that H-20's exit-gate checklist references.

## Notes
