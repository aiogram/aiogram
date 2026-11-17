# I-22 — 3 → 4 migration rehearsal (milestone I exit gate)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-16](I-16-codemod-imports-removals.md), [I-17](I-17-model-semantics-rules.md), [I-18](I-18-positional-to-keyword-rule.md), [I-19](I-19-heuristic-behaviour-rules.md), [I-20](I-20-examples-port-smoke.md), [I-23](I-23-beta-pre-release.md), [3x-24](../3x-quick-wins/3x-24-migration-baseline-release.md), [I-14](I-14-migrate-engine.md) |
| Blocks | [J-01](../J-ga/J-01-feature-inventory-audit.md), [J-02](../J-ga/J-02-migration-guide-completion.md) |
| Gate-conditional | no |
| Decisions | D74, D82, D100, PD-02, R28 |
| Sources | [README milestone I](../../research/README.md), [16-support-policy.md §2](../../research/16-support-policy.md), [18-docs-migration.md §2](../../research/18-docs-migration.md), [codex-review R28](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Milestone I's exit gate requires a 3→4 migration rehearsal across Tier 1. R28 notes that accepting the removals doesn't
validate every claimed automatic migration. The tools must be measured on real code, and the guide must be honest about
coverage. I-20 rehearsed on the official examples. This plan rehearses on real third-party projects using the published
beta (I-23), exactly as users will (`uvx --from 'aiogram[migrate]>=4.0.0b1' …`).

## Scope

**In:**
- **Corpus** of at least 5 public, permissively licensed aiogram 3.x bots of different sizes (small single-file,
  multi-router, FSM + scenes, webhook, i18n), plus:
  - the 3.x `examples/` (from I-20);
  - code blocks extracted from the 3.x docs.
  - Pin each project's commit and record its license in `tests/migration_corpus/manifest.toml`. Store only the manifest
    and fetch at run time; don't vendor third-party code unless the license allows it.
- **Per project:**
  1. `check --format json` on 3.x source;
  2. `fix --write`, then `fix --heuristic --write` on a copy;
  3. install the beta, run the project's own tests if it has any, or an import + dispatcher build smoke;
  4. manually list the remaining errors.
- **Metrics per finding class.** Found, fixed, false positive, missed (a manual diff against what was actually needed),
  and the share of D100 calls fixed definite / heuristic / manual.
- **Fix-forward.** Each false positive or miss goes to a rule fix (small PRs against I-16 to I-19, or extra golden
  cases) or a guide note (J-02).
- **Tier 1 coverage.** The tool runs on Linux, macOS and Windows (path handling, CRLF files).
- **Report.** `tests/migration_corpus/REPORT.md`, generated, with a summary table that J-02's start page quotes.

**Out:**
- Guide prose (J-02).
- Install rehearsal (I-21).

## Checklist

- [ ] Choose the corpus and record the manifest (commit, license, size).
- [ ] Runner script `scripts/migration_rehearsal.py`: fetch, run `check` / `fix`, collect JSON, run smoke, emit the report.
- [ ] CI workflow (`workflow_dispatch` + weekly until GA) on ubuntu / macOS / windows.
- [ ] Triage every false positive and miss. Link each to a fix PR or a guide note in Notes.
- [ ] **Exit-gate thresholds (decide, proposed default):**
      - zero definite-class false positives;
      - zero rewrites that break `compile()`;
      - ≥ 90% of positional API calls in the corpus fixed by `fix --heuristic`;
      - every remaining incompatibility appears as a finding or a manual-checklist item.
      Record the thresholds in Notes and flag them to the owner.
- [ ] Tests for the runner script's report generator (100% coverage).
- [ ] No changelog fragment (internal); registry coverage fields updated if rehearsal changes them.

## Acceptance criteria

- The report exists for the pinned corpus on all three OSes.
- The thresholds above (or owner-revised ones recorded in Notes) are met.
- Every miss has a linked fix PR or guide entry.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Rehearsing only on the official examples | Not representative of user code | R28 |
| Vendoring third-party bots into the repo | License / size; manifest + fetch instead | (this plan) |
| Running the tools from a dev checkout | Users run the published beta via `uvx` | R28, I-23 |

## Validation

```bash
uvx --from 'aiogram[migrate]==4.0.0b1' aiogram migrate check tests/migration_corpus/examples_3x
uv run python scripts/migration_rehearsal.py --manifest tests/migration_corpus/manifest.toml
uv run pytest tests/test_migrate tests/ci -q
make lint
```

## Workflow notes

- Inputs: I-16 to I-19 (rules), I-20 (examples report), I-23 (published beta).
- Outputs: coverage numbers for J-02 and the I exit evidence for J-01.

## Notes

(empty)
