# J-04 — 4.0.0 release notes and published 3.x support dates

| Field | Value |
|---|---|
| Status | `todo` |
| Story | J — GA |
| Target branch | `dev-4.x` (the `dev-3.x` companion is [J-08](J-08-3x-support-banner-dates.md)) |
| Depends on | [J-01](J-01-feature-inventory-audit.md), [J-03](J-03-beta-triage-p1-signoff.md), [3x-24](../3x-quick-wins/3x-24-migration-baseline-release.md) |
| Blocks | [J-07](J-07-ga-cut-rtd-switch.md), [J-08](J-08-3x-support-banner-dates.md) |
| Gate-conditional | no |
| Decisions | D71, D73, D6 (ledger window), D20, D74, D121, PD-01 |
| Sources | [16-support-policy.md D71–D74](../../research/16-support-policy.md), [02-butcher.md §4](../../research/02-butcher.md), [README breaking changes, roadmap](../../research/README.md), `4.x-plan-for-core-devs.md` (closed circulation, not in this repository) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D73: after **4.0.0 GA**, 3.x gets 12 months of full support (Bot API bumps via the legacy butcher, bugfixes, 09 quick
wins), then 6 months security-only, then EOL. The exact dates are published in the 4.0.0 release notes and docs. The
clock starts at GA, not at `4.0.0a1` or the beta (D121).

The J gate requires published dates. The release notes are also users' first contact with 24 breaking changes, so they
must lead with the migration path.

## Scope

**In:**
- **Release notes `4.0.0`** (towncrier output plus a hand-written header in `CHANGES.rst` and the docs Changelog):
  - highlights (4.x-plan "What changes for users");
  - "How to migrate" (`aiogram migrate check` → `fix`, guide link);
  - breaking changes 1–24, each linked to its guide item;
  - the deferred list from J-01;
  - platforms (Tier 1 / best-effort, ft; "PyPy is not supported in 4.x; stay on 3.x", PD-35);
  - the 3.x support dates.
- **Dates.** `GA = <tag date>`, `full support until = GA + 12 months`, `security-only until = GA + 18 months`. They are
  published in:
  - the 4.0.0 release notes;
  - the docs "Support policy" page (`dev-4.x`);
  - the 3.x docs banner and `README.rst` on `dev-3.x` (J-08, from this plan's script output);
  - a pinned GitHub discussion or announcement.
- **Support policy page** (`dev-4.x`):
  - D71, one deprecation window: the later of 12 months and 2 minors, removals in minors, the 4.0 reset as an explicit
    exception;
  - the Bot API ledger window (D6: later of 12 months and 2 Bot API majors);
  - Python floor policy (D20: 3.11 dropped in a 4.x minor after Oct 2027);
  - a prominent note that removals happen in 4.x minors, so `<5` doesn't mean no breaks (R28).

**Out:**
- The `dev-3.x` banner, README support line and 3.x butcher-maintenance statement (J-08).
- Tagging (J-07).
- RTD switch (J-07).

## Checklist

- [ ] Compute the dates from the planned GA tag date. If the tag slips, re-run before J-07 (a single script
      `scripts/support_dates.py --ga YYYY-MM-DD` prints all three dates).
- [ ] Release-notes header and body. towncrier build on `dev-4.x`.
- [ ] Support policy docs page.
- [ ] Announcement draft.
- [ ] Tests for `support_dates.py` (leap-year GA date, month-end date), 100% coverage.
- [ ] Changelog: the 4.0.0 towncrier build (this *is* the changelog).

## Acceptance criteria

- The same three dates appear in the 4.0.0 notes and the 4.x Support policy page. A docs test greps them against
  `support_dates.py` output (J-08 checks the 3.x side against the same output).
- Every README breaking change 1–24 in the release notes links to a guide anchor (link check in the docs build).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Starting the 3.x clock at `4.0.0a1` / beta | Clock starts at GA | D73, D121 |
| Dates only in the docs | Release notes and docs both | D73 |

## Validation

```bash
# on dev-4.x
uv run python scripts/support_dates.py --ga <date>
grep -n "<full-support date>" CHANGES.rst docs/support-policy.rst   # support page path per I-10
grep -n "<security-only date>" CHANGES.rst docs/support-policy.rst
uv run pytest tests/test_support_dates.py tests/docs -q
uv sync --group docs --no-install-project && uv run --no-sync bash -c 'cd docs && make html SPHINXOPTS=-W'
```

## Workflow notes

- Inputs: J-01 (deferred list, inventory), J-03 (sign-off date drives the planned GA date), 3x-24 (baseline release name).
- Outputs: notes and dates used by J-07; the `support_dates.py` output J-08 copies to `dev-3.x`.

## Notes

(empty)
