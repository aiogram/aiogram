# A-07 — Differential harness framework (two venvs, canonical traces, difference manifests, poison control)

| Field | Value |
|---|---|
| Status | `done` |
| Story | A — Contracts & baselines |
| Target branch | `dev-3.x` (merged forward to `dev-4.x`, PD-12) |
| Depends on | [A-04](A-04-pinned-corpus.md) |
| Blocks | [A-08](A-08-model-oracle.md), [A-09](A-09-request-oracle.md), [A-10](A-10-routing-oracle.md), [D-15](../D-client/D-15-request-response-differential-cases.md), [E-21](../E-runtime/E-21-e-exit-gate.md), [E-02](../E-runtime/E-02-dispatch-table-executor.md), [H-16](../H-testing-observability/H-16-fake-fidelity.md) |
| Gate-conditional | no (approved-difference entries for gate-dependent decisions are tagged `gate = true`) |
| Decisions | 13 B8, R26, PD-12, D104 |
| Sources | [08 §5 Differential harnesses](../../research/08-build-release.md), [13 B8](../../research/13-aiogram-rust-review.md), [14 §3 Fidelity / Difference manifests](../../research/14-testing.md), [19 R26](../../research/19-review-resolutions.md), [codex-review R26](../../research/codex-review.md), [README breaking changes](../../research/README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The behaviour oracle (PD-12) is an **external pinned 3.x venv**. 4.0 carries no in-tree reference path. 13 B8:
aiogram_rust's model, request and routing traces compared across two venvs found 4 real model bugs in 2 800 cases,
and native and fallback encoders disagreed on 12 of 300 requests. A poisoned side must produce mismatches, or the
harness counts as broken.

R26: 4.0 *intends* many differences, so unconditional parity is wrong. Each case is classed:
- **invariant**;
- **approved difference**, with a decision id and a narrow assertion;
- **newly supported**.

The same framework also checks 3.x against patched 3.x for the quick wins (D120), so it must be version-agnostic.

## Scope

**In.** Proposed layout and CLI (plans cite this CLI):

```
differential/
  __main__.py                       # CLI
  runner.py                         # venv management, side execution, comparison
  trace.py                          # canonical JSONL record format
  manifests/{model,request,routing}.toml
  sides/aiogram3/{model,request,routing}.py   # 3.x adapters (A-08..A-10)
  sides/aiogram4/                   # added by B/D/E plans
uv run python -m differential run --kind <model|request|routing|smoke> --left <side> --right <side> [--poison left|right]
  side := pypi:aiogram==3.32.0 | git:<ref> | path:<dir>
```

- **Venvs:**
  - each side gets its own venv under `.differential/venvs/<hash>`, created with `uv venv` plus `uv pip install`
    (pypi), or a `git worktree` plus `uv pip install <worktree>` (git/path);
  - side scripts are **standalone** (stdlib + aiogram only) and run with `python -I <script> --corpus <dir> --out
    <trace.jsonl>`, so nothing from the repo leaks into the side's import path;
  - the adapter (`sides/aiogram3` or `sides/aiogram4`) is chosen from `aiogram.__version__`.
- **Canonical trace record** (JSON, sorted keys, one per line): `{case, probe, ok, value | error: {type, attrs},
  meta}`. Floats are canonical repr, bytes are base64, sets are sorted lists, and values that aren't JSON-native
  have a `__kind__` tag.
- **Manifest** per kind:
  ```toml
  [[case]]
  match = "model.update.realistic.*"   # glob over case/probe
  class = "invariant"                  # invariant | approved | new
  decision = "D86"                     # required for approved/new; plan ids (e.g. 3x-09) allowed for 3.x-vs-3.x
  assert = "wire_names_in_dump_json"   # named comparator in runner.py, required for approved
  gate = false                         # true when the decision is gate-dependent (D104)
  ```
  Unmatched cases default to `invariant`.
- **Comparators:**
  - `invariant` → exact equality;
  - `approved` → the named narrow assertion must hold, and the rest of the record must still be equal;
  - `new` → left failed and right succeeded.
- **Poison control.** `--poison <side>` corrupts that side *inside its process*: the adapter receives `--poison` and
  perturbs real behaviour, for example flipping one field per decoded object, dropping a param, or swapping handler
  order. The harness must then report ≥ 1 mismatch per kind; if it doesn't, it exits non-zero. CI runs every kind
  once in poison mode.
- **Seed approved differences** for the 4.0 decisions known now, from README breaking changes 1–24, as
  `[[case]]` stubs with `match` patterns to be refined by A-08..A-10 and the 4.0 plans:
  - D84 / D108 (equality ignores the bot);
  - D86 (wire names);
  - D87 (JSON-shaped extras);
  - D94;
  - D106 (tuples);
  - D107 (Unknown absorbs malformed members);
  - D10 / 10 Layer 2 (new);
  - D103 (`as_()` returns a new view);
  - D111;
  - breaking change 13 (compiled rejector skip);
  - D48;
  - D34;
  - D28 / D110;
  - D114;
  - D12;
  - R18 (JSON body).
- **Report:** a summary table per class and a diff of the first N mismatches. Exit code ≠ 0 on any unapproved
  mismatch.

**Out:**
- The probes per kind: A-08 (model), A-09 (request / response), A-10 (routing).
- 4.0 adapters: B/D/E plans (e.g. D-15).

## Checklist

- [ ] Implement venv management, side execution, trace format, comparators, manifest loader and CLI.
- [ ] Add a trivial `sides/aiogram3/smoke.py` kind (decode `update.text.small` and dump it) to test the framework end
      to end before A-08 exists.
- [ ] Poison mode, plus the self-check that fails when poison produces no mismatch.
- [ ] Seed the approved-difference stubs listed above. Mark `gate = true` for D83–D87, D91–D95, D103 and D106–D108.
- [ ] Self-tests (`tests/test_differential_framework.py`). They run in CI, using a fake side: two in-process
      functions, no venvs.
  - Cover each comparator, manifest glob matching and the poison self-check.
- [ ] A CI job (on demand plus weekly): `run --kind smoke --left pypi:aiogram==<latest 3.x> --right path:.`, plus the
      same with `--poison right`. Run `make lint-workflows`.
- [ ] `differential/README.md`: concepts, CLI and how a plan adds an approved difference.
- [ ] Exclude `differential/` from packaging and verify.
- [ ] Changelog: none. Use the `skip news` label.

## Acceptance criteria

- `run --kind smoke --left git:HEAD --right path:.` on a clean tree reports 0 mismatches.
- `--poison right` reports ≥ 1 mismatch and exits non-zero. If the poisoned run found nothing, the harness itself
  exits non-zero with "poison not detected".
- Every seeded approved entry names a decision id and a comparator.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| In-tree 3.x reference path inside 4.0 | No dead reference code in 4.0; the oracle is an external pinned venv | PD-12 |
| Unconditional 3.x parity | 4.0 intends documented differences | R26 |
| Broad snapshot exclusions | Approved differences need a narrow assertion and a decision id | R26 |
| Deriving expected values from the same IR as the implementation | Can miss a wrong mapping; hand-curated fixtures and recorded traces are needed | R26 |

## Validation

```bash
uv run pytest tests/test_differential_framework.py -q
uv run python -m differential run --kind smoke --left git:HEAD --right path:.
uv run python -m differential run --kind smoke --left git:HEAD --right path:. --poison right; test $? -ne 0
make lint
make lint-workflows
```

## Workflow notes

- **Outputs:** the framework, the manifest schema and the seeded approved-difference list. A-08..A-10 add the 3.x
  probes. D-15 (request/response), E-21 (routing) and the B plans (model) add 4.0 adapters, and each turns its
  decisions' stubs into concrete assertions.
- The `gate = true` entries are void if B-13 is a no-go.

## Notes
