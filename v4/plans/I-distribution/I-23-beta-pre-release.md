# I-23 — 4.0 beta pre-release

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-02](I-02-tier1-wheel-matrix-release.md), [I-04](I-04-installed-wheel-typing-stubtest.md), [I-09](I-09-import-free-docs-build.md), [I-10](I-10-diataxis-docs-skeleton.md), [I-16](I-16-codemod-imports-removals.md), [I-17](I-17-model-semantics-rules.md), [I-18](I-18-positional-to-keyword-rule.md), [I-19](I-19-heuristic-behaviour-rules.md), [I-20](I-20-examples-port-smoke.md), [I-21](I-21-fresh-machine-install-rehearsal.md), [C-25](../C-butcher/C-25-historical-scenario-tests.md), [D-16](../D-client/D-16-cancellation-resource-tests.md), [E-21](../E-runtime/E-21-e-exit-gate.md), [F-16](../F-fsm/F-16-race-suite-314t.md), [H-20](../H-testing-observability/H-20-integration-layer-exit-gate.md), [G-21](../G-features/G-21-aiogram-cli-final-release.md) |
| Blocks | [I-22](I-22-migration-rehearsal.md), [J-03](../J-ga/J-03-beta-triage-p1-signoff.md) |
| Gate-conditional | no |
| Decisions | D121, PD-01, D119, PD-27 |
| Sources | [README roadmap](../../research/README.md), [19 D121](../../research/19-review-resolutions.md), [18-docs-migration.md §1 (RTD)](../../research/18-docs-migration.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`4.0.0a1` is an alpha, not GA (D121). The beta is the first release in which the full feature set is in place (PD-01),
as is the migration tooling, so users can rehearse their own migration with
`uvx --from 'aiogram[migrate]>=4.0.0b1' aiogram migrate check`.

J-03 collects feedback from this release. The 3.x support clock does **not** start here (D73 starts at 4.0.0 GA).

## Scope

**In:**
- **Feature-complete check:** every plan in stories C, D, E, F, G and H has `Status: done` or `dropped` with a reason.
  The exit gates are C-25, D-16, E-21, F-16 and H-20; for G, every G plan, with G-21 the last.
- Version `4.0.0b1` via the I-01 version source. Changelog built with towncrier on `dev-4.x`.
- Publish through the I-02 workflow: Tier 1 is blocking, best-effort follows.
- PyPI pre-release: plain `pip install aiogram` keeps resolving 3.x. This is verified in a fresh venv.
- RTD: the `dev-4.x` version is public and linked from the 3.x docs banner as "4.0 beta". `latest` stays on 3.x until J-07.
- **Feedback channel.** A GitHub issue template `4.0 beta feedback` and a label `4.0-beta`. The migration guide start
  page asks users to run `check` and report misses with `--format json` output attached.
- Announcement text (blog / chat) pointing at the guide and the migrate tool.

**Out:**
- Triage (J-03).
- GA (J-07).

## Checklist

- [ ] Verify the dependency plans are `done`. List any `dropped` plans with their reasons in Notes.
- [ ] Bump to `4.0.0b1`. Set `Development Status :: 4 - Beta` (I-01).
- [ ] Run the I-21 rehearsal on the release candidate artifacts before tagging.
- [ ] Tag, then run the I-02 release.
- [ ] Fresh venv: `pip install aiogram` installs 3.x, and `pip install --pre aiogram` installs `4.0.0b1`.
- [ ] RTD `dev-4.x` public, plus a 3.x docs banner (small `dev-3.x` PR).
- [ ] Issue template and label.
- [ ] Changelog: the towncrier build for `4.0.0b1` (fragments consumed).

## Acceptance criteria

- `4.0.0b1` on PyPI with all 49 Tier-1 wheels and an sdist.
- `uvx --from 'aiogram[migrate]==4.0.0b1' aiogram migrate check examples_3x/` works on a machine with only `uv` installed.
- The RTD `dev-4.x` build is green and public.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Treating `4.0.0a1` as GA / starting the 3.x clock | Alpha ≠ GA; clock starts at GA | D121, D73 |
| Beta without the full feature set | Full D121 set blocks GA; the beta must carry it to be meaningful | PD-01 |

## Validation

```bash
gh workflow run install-rehearsal.yml -f version=4.0.0b1
gh workflow run release.yml   # after tagging v4.0.0b1
uv venv /tmp/b && uv pip install --python /tmp/b/bin/python aiogram && /tmp/b/bin/python -c "import aiogram; print(aiogram.__version__)"
```

## Workflow notes

- Inputs: all story exit gates.
- Outputs: the beta that I-22 (rehearsal on real projects) and J-03 (triage) use.

## Notes

(empty)
