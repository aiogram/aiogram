# I-20 — Port `examples/` to 4.0 and run them in CI

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-10](I-10-diataxis-docs-skeleton.md), [I-16](I-16-codemod-imports-removals.md), [I-17](I-17-model-semantics-rules.md), [I-18](I-18-positional-to-keyword-rule.md), [H-20](../H-testing-observability/H-20-integration-layer-exit-gate.md), [E-21](../E-runtime/E-21-e-exit-gate.md), [F-16](../F-fsm/F-16-race-suite-314t.md), [G-10](../G-features/G-10-utils-removals.md), [I-14](I-14-migrate-engine.md) |
| Blocks | [I-22](I-22-migration-rehearsal.md), [I-23](I-23-beta-pre-release.md) |
| Gate-conditional | no (re-validate after B-13: examples use the model API) |
| Decisions | D74, D80, D88, D100, D103, 18 §1 |
| Sources | [18-docs-migration.md §1](../../research/18-docs-migration.md), [14-testing.md §3](../../research/14-testing.md), [11-removals.md §4](../../research/11-removals.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

18 §1 rewrites `examples/` for 4.0 and runs them in CI as smoke tests through the testing toolkit (14). Docs embed them
with `literalinclude`, so the snippets are tested.

The 3.x tree has `context_addition_from_filter.py`, `echo_bot.py`, `echo_bot_webhook.py`, `echo_bot_webhook_ssl.py`,
`error_handling.py`, `finite_state_machine.py`, `multi_file_bot/`, `multibot.py`, `own_filter.py`, `quiz_scene.py`,
`scene.py`, `specify_updates.py`, `stars_invoice.py`, `web_app/`, `without_dispatcher.py` and `data/`. Three files use
`utils.markdown` (11 §4).

The port doubles as the first **migration rehearsal**: run `aiogram migrate fix` on the 3.x tree, diff the result
against the hand port, and record what the tool missed.

## Scope

**In:**
- **Examples split (agreed with H-20):** H-20 builds the smoke helper and ports + wires 3 polling-style examples
  (named in H-20's *Notes*); this plan ports the **remaining** examples and registers them with H-20's helper.
- Port every remaining example to the 4.0 API:
  - keyword-only calls;
  - formatting nodes instead of `utils.markdown`;
  - Runner / `run_polling` wrappers;
  - `event_context`;
  - typed FSM data where natural.
- **Rehearsal step:**
  1. copy the 3.x tree to `tests/migration_corpus/examples_3x/` (frozen input);
  2. run `aiogram migrate fix --write` (default classes) and `--heuristic`;
  3. commit the tool output diff against the hand port as a report in Notes and in
     `tests/migration_corpus/examples_report.json` (count of definite / heuristic / missed changes).
- **Smoke tests** registered with H-20's examples-smoke runner:
  - polling-style examples are driven through the toolkit (`WorldSource`, 14 §3);
  - webhook, SSL, `web_app/` and `without_dispatcher.py` get an **app-build smoke**: import, build the aiohttp app or
    the method object, no network, because the toolkit is typed-level and single-loop (14 §3) and doesn't cover them.
- `literalinclude` wiring in the I-10 tree (Tutorial / How-to pages referencing examples).

**Out:**
- The smoke runner itself and the 3 examples H-20 wires (H-20).
- New examples beyond the 3.x set: optional, only where a Tutorial page needs one, and the page owner adds it.

## Checklist

- [ ] Freeze the 3.x examples input. Run both `fix` modes and save the report.
- [ ] Hand-port each remaining example (all but H-20's 3) and register each with the H-20 smoke runner (toolkit or
      app-build mode).
- [ ] Diff tool output vs hand port. File each miss as a Notes entry with the responsible rule plan (I-16 to I-19).
- [ ] `literalinclude` in the Tutorial pages: first bot = `echo_bot.py`, FSM = `finite_state_machine.py`, scenes =
      `scene.py` / `quiz_scene.py`, webhook = `echo_bot_webhook.py`, multi-bot = `multibot.py`.
- [ ] `ruff` + `mypy --strict` over `examples/` against the installed wheel (types must match the stubs).
- [ ] Tests (the smoke tests are the tests). No coverage requirement on example code itself.
- [ ] Changelog fragment `CHANGES/<id>.doc.rst` (examples ported to 4.0).

## Acceptance criteria

- Every example passes its smoke test in CI on the PR matrix (I-05).
- The import-free docs build (I-09) renders all `literalinclude`s with no missing-file warnings.
- `examples_report.json` exists and lists the definite / heuristic / missed counts per example.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Untested docs snippets | Docs embed `examples/` so snippets are tested | 18 §1 |
| Running webhook examples through the toolkit | Toolkit is typed-level and single-loop | 14 §3 |
| Rewriting the whole test suite with the toolkit | MockedBot stays for unit tests | D88 |

## Validation

```bash
make dev
uv run pytest tests/test_examples -q   # H-20's runner path
uv run mypy --strict examples
uv run pytest tests
make lint
uv sync --group docs --no-install-project && uv run --no-sync bash -c 'cd docs && make html SPHINXOPTS=-W'
```

## Workflow notes

- Inputs:
  - I-16 to I-18 (rules), I-10 (docs tree);
  - H-20 (smoke runner);
  - E-21, F-16 (stable runtime and FSM APIs);
  - the G features used by examples (formatting G-08, i18n G-03 if an example uses it).
- Outputs: the examples report (I-22 baseline), tested snippets (J-02).
- **Split with H-20 (settled):** H-20 owns the smoke helper and 3 wired examples; this plan ports and registers the
  rest. Both plans state the same split; do not re-port H-20's three.

## Notes

(empty)
