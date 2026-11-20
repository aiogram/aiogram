# H-18 — Toolkit and observability docs (4.0 structure)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-14](H-14-delivery-through-runner.md), [H-15](H-15-route-diagnostics-on-trace-hook.md), [H-17](H-17-toolkit-feature-interop.md), [I-10](../I-distribution/I-10-diataxis-docs-skeleton.md) |
| Blocks | [H-20](H-20-integration-layer-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D89, D80, D100, D51, D54 |
| Sources | [14-testing.md §3 "OpenSpec"](../../research/14-testing.md), [18-docs-migration.md](../../research/18-docs-migration.md), [15-observability.md](../../research/15-observability.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

With OpenSpec dropped (D89), `docs/dispatcher/testing.rst` (3 580 lines, imported by H-10) is the toolkit's
specification. It is written against 3.x:
- positional calls;
- the auto-loaded plugin;
- middleware-injected diagnostics;
- `detach_router`.

It must move into the D80 (Diátaxis) structure and describe 4.0 behaviour.

## Scope

**In:**
- Split `testing.rst` into the I-10 skeleton:
  - **tutorial**: first toolkit test;
  - **how-tos**: FSM/scenes, flood/retry, unknown updates, i18n, dependency overrides, lifecycle with
    `running()`, multi-bot;
  - **reference**: fixtures, actors, `env.on`/`blocked`, call records with `source`, rejections;
  - **explanation**: what the fake models vs synthesises (R26), identity scope (H-13 decision), single-loop
    limitation.
- Rewrite all examples:
  - keyword-only calls (D100);
  - no plugin setup step: the plugin loads on its own through the `pytest11` entry-point shim, and examples that
    show the switch use `-p no:aiogram` to turn it off, never `-p aiogram.test.plugin` (TW-188; D51 as revised
    2026-11-19, see H-10's Notes);
  - no `detach_router`;
  - diagnostics via the trace hook.
- Every code block in the toolkit docs is a test. Use the existing docs-doctest mechanism if I-10 provides one;
  otherwise a `tests/test_testing/test_docs_examples.py` that runs the extracted blocks.
- Collect the observability docs written by H-01/H-02/H-04/H-05/H-08/H-09 under one "Logging & observability"
  section of the skeleton (moving only, no new content).

**Out:**
- uk_UA translation (I-11).
- API reference generation (I-09).
- Migration guide pages (J-02, I-12).

## Checklist

- [ ] Split and rewrite `testing.rst` into the skeleton.
- [ ] Docs-example tests.
- [ ] Observability section assembled.
- [ ] Remove the old single page, or leave a redirect stub if I-10 defines redirects.
- [ ] Docs build passes.
- [ ] No changelog fragment (docs-only), unless the project files docs changes as `doc` fragments. If so, add a
      `CHANGES/<id>.doc.rst`.

## Acceptance criteria

- No positional call to a generated method or constructor remains in the toolkit docs. A guard checks this through
  the I-18 checker, or with a regex test until I-18 exists.
- All extracted examples run green in `uv run pytest tests`.
- The docs build has no warnings for the new pages.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keeping OpenSpec as the spec | Dropped | D89 |
| One 3.5k-line page | Doesn't fit the D80 structure | D80 |

## Validation

```bash
uv run --extra docs bash -c 'cd docs && make html'   # or the I-09 import-free docs command once it exists
uv run pytest tests
make lint
```

## Workflow notes

- Inputs:
  - I-10: skeleton;
  - H-14/H-15/H-17: behaviour to document;
  - the H-13 identity decision (gate-conditional content, so mark that section for re-check after B-13).
- I-11 picks up the narrative pages for translation.

## Notes
