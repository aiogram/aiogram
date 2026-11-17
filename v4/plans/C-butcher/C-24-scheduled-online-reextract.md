# C-24 — Scheduled online re-extract job

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-02](C-02-fetch-provenance.md), [C-08](C-08-merge-cross-check.md), [C-11](C-11-import-legacy.md) |
| Blocks | — |
| Gate-conditional | no |
| Decisions | D118, PD-10, D73 |
| Sources | [19 D118](../../research/19-review-resolutions.md), [02-butcher.md §5, §6](../../research/02-butcher.md), [codex-review.md R24](../../research/codex-review.md), [plans README PD-10](../README.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

PR CI is offline (C-23), so a separate scheduled job notices drift:
- the live HTML or schema changed for the same API version;
- a new API version appeared;
- the OpenAPI source caught up with the HTML;
- a legacy 3.x overlay change hasn't been ported (PD-10 diff mode, until D73 full support ends).

## Scope

**In:** `.github/workflows/butcher-reextract.yml`, on a daily cron and `workflow_dispatch`:
- `cargo xtask butcher fetch` then `build` into a temp snapshot, then diff the per-adapter IRs against the committed
  `butcher/snapshots/<current>/ir.*.json`;
- on a difference: open or update **one** issue labelled `butcher-drift` with the C-08 disagreement report and the
  `butcher diff` change list, and attach the raw bundle as a workflow artifact;
- `cargo xtask butcher import-legacy --diff --legacy-dir <dev-3.x checkout>/.butcher` (C-11), with the result in the same issue;
- least-privilege permissions (`issues: write`, `contents: read`), pinned actions, zizmor-clean.

**Out:** opening PRs with regenerated code (a maintainer runs the bump); the release asset upload (I-02).

## Checklist

- [ ] Workflow file with cron, dispatch, permissions and pinned actions.
- [ ] Issue create/update step (idempotent: one open drift issue at a time).
- [ ] dev-3.x checkout step plus the legacy diff mode.
- [ ] Remove the legacy diff step when 3.x full support ends; write a dated Notes reminder here and in C-11.
- [ ] `make lint-workflows` passes; with `GH_TOKEN=$(gh auth token)` too, to match CI's online audits.
- [ ] Tests: a dry run via `workflow_dispatch` on a fork with a doctored committed IR opens the issue.

## Acceptance criteria

- With the committed IR equal to live, the job finishes green and opens nothing.
- With one field removed from the committed `ir.html.json` (test branch), the job opens exactly one `butcher-drift` issue naming that field.
- A second run with the same drift updates the existing issue instead of opening a new one.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Online extraction in PR CI | PR CI must be offline | D118 |
| Auto-PR with regenerated code | Bumps need overlay decisions (C-08, C-09 rules) | 02 §2 |

## Validation

```bash
rtk proxy make lint-workflows
GH_TOKEN=$(gh auth token) rtk proxy make lint-workflows
gh workflow run butcher-reextract.yml --ref <test-branch>
```

## Workflow notes

- Reuses C-02 (`fetch`) and C-08 (report). The legacy diff mode comes from C-11.

## Notes
