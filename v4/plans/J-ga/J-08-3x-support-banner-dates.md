# J-08 — 3.x companion: support banner, dates and README on `dev-3.x`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | J — GA |
| Target branch | `dev-3.x` |
| Depends on | [J-04](J-04-release-notes-3x-support-dates.md), [3x-24](../3x-quick-wins/3x-24-migration-baseline-release.md) |
| Blocks | [J-07](J-07-ga-cut-rtd-switch.md) |
| Gate-conditional | no |
| Decisions | D73, D121 |
| Sources | [16-support-policy.md D73](../../research/16-support-policy.md), [README roadmap](../../research/README.md), `4.x-plan-for-core-devs.md` (closed circulation, not in this repository) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D73: after 4.0.0 GA, 3.x gets 12 months of full support, then 6 months security-only, then EOL. 3.x users mostly read
the 3.x docs and the PyPI README, not the 4.0 release notes, so the dates must also be published on `dev-3.x`. J-04
computes the dates and publishes them on `dev-4.x`; this plan carries the same dates to the 3.x branch.

## Scope

**In** (`dev-3.x` PR):
- **3.x docs banner**: furo's `announcement` entry in `html_theme_options` in `docs/conf.py` (the 3.x docs use the
  furo theme; today `html_theme_options = {}`), stating the three dates (GA, full support until, security-only until) and linking the 4.x
  migration guide.
- **`README.rst` support line** with the same dates.
- The migration-baseline release (3x-24) is named in both.
- A statement that the 3.x legacy butcher stays maintained until the full-support end (D73).
- Changelog fragment `CHANGES/<id>.doc.rst` on `dev-3.x`.

**Out:**
- Computing the dates, the 4.0.0 release notes and the 4.x Support policy page (J-04).
- Tagging and the RTD switch (J-07).

## Checklist

- [ ] Take the three dates from J-04's `scripts/support_dates.py --ga <date>` output (run on `dev-4.x`) and record the
      command and output in Notes.
- [ ] Docs banner on `dev-3.x`: set `html_theme_options["announcement"]` in `docs/conf.py`.
- [ ] `README.rst` support line.
- [ ] Name the 3x-24 baseline release and the butcher-maintenance end date.
- [ ] Changelog fragment `CHANGES/<id>.doc.rst`.
- [ ] If the GA date moves, re-run with J-04 and update this PR before J-07.

## Acceptance criteria

- The three dates in the 3.x banner and `README.rst` equal J-04's `support_dates.py` output for the planned GA date
  (grep check below).
- The banner links resolve: the 3.x docs build with `-W` and the link check passes.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Dates only in the 4.0 release notes | 3.x users read the 3.x docs and README | D73 |
| One PR across both branches | Each branch needs its own validation and review | branch policy (A-01) |

## Validation

```bash
# on dev-3.x
grep -n "announcement" docs/conf.py
grep -n "<full-support date>" README.rst docs/conf.py
grep -n "<security-only date>" README.rst docs/conf.py
uv run --extra docs bash -c 'cd docs && make html SPHINXOPTS=-W'
uv run --extra docs bash -c 'cd docs && make linkcheck'
make lint
```

## Workflow notes

- Inputs: J-04 (the dates), 3x-24 (baseline release name).
- Outputs: the published 3.x dates J-07 checks before the cut.

## Notes
