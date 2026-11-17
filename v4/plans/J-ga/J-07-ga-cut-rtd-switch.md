# J-07 — 4.0.0 GA cut and Read the Docs `latest` switch

| Field | Value |
|---|---|
| Status | `todo` |
| Story | J — GA |
| Target branch | `dev-4.x` |
| Depends on | [J-01](J-01-feature-inventory-audit.md), [J-02](J-02-migration-guide-completion.md), [J-03](J-03-beta-triage-p1-signoff.md), [J-04](J-04-release-notes-3x-support-dates.md), [J-05](J-05-release-ownership-runbook-rollback.md), [J-06](J-06-external-package-releases.md), [I-02](../I-distribution/I-02-tier1-wheel-matrix-release.md), [J-08](J-08-3x-support-banner-dates.md) |
| Blocks | — |
| Gate-conditional | no |
| Decisions | D73, D121, PD-01, PD-27, 18 §1 (RTD) |
| Sources | [18-docs-migration.md §1](../../research/18-docs-migration.md), [16-support-policy.md D73](../../research/16-support-policy.md), [README milestone J](../../research/README.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

GA is the point where:
- the 3.x support clock starts (D73);
- `pip install aiogram` resolves 4.x;
- Read the Docs `latest` switches from 3.x to 4.x (18 §1).

All J gates must be green first.

## Scope

**In:**
- **Pre-flight**, per J-05's runbook:
  - J-01 inventory green;
  - J-03 sign-off;
  - J-04 notes and dates final for the actual tag date (re-run `support_dates.py` if the date moved), and J-08's 3.x
    banner and README carry the same dates;
  - J-06 external releases out;
  - I-21 and I-22 green on the final rc.
- **Version.** `4.0.0`. Classifier `Development Status :: 5 - Production/Stable` (I-01).
- **Tag and release** via the I-02 workflow. Then the post-release smoke from PyPI on each Tier-1 OS.
- **Read the Docs:**
  - `latest` → `dev-4.x` / `4.0.0`;
  - `stable` → the 4.0.0 tag;
  - the 3.x docs stay available as a named version (`3.x` / `dev-3.x`) with `migration_2_to_3` (18 §1);
  - the uk_UA project follows the same switch (I-11; partial translation allowed).
- **Repository:**
  - GitHub default branch → `dev-4.x` (owner decision; record it);
  - README badges and links;
  - close milestones I and J;
  - set the plan statuses to `done`.
- **Announcements** (J-04 draft), with the 3.x dates.

**Out:**
- Anything that fails pre-flight: stop and reopen the owning plan.

## Checklist

- [ ] Run the J-05 pre-flight. Record the result in Notes.
- [ ] Confirm the GA date equals the date used in J-04. Otherwise update J-04's outputs first.
- [ ] Bump to `4.0.0`, towncrier build, tag `v4.0.0`, run the I-02 release.
- [ ] Post-release PyPI smoke on Linux, macOS and Windows (`pip install aiogram` resolves 4.0.0 and `aiogram info` works).
- [ ] RTD: switch `latest` / `stable`, keep the 3.x version, verify redirects for common 3.x URLs land on the 3.x
      version or the 4.x equivalent.
- [ ] **Decide whether to switch the GitHub default branch to `dev-4.x` at GA** (proposed default: yes, at GA; `dev-3.x`
      stays protected for maintenance until 3.x EOL). Record it in Notes and flag it to the owner.
- [ ] Announcement published.
- [ ] Changelog: the 4.0.0 build (consumes all `dev-4.x` fragments).

## Acceptance criteria

- `pip install aiogram` in a clean venv on each Tier-1 OS installs 4.0.0 from a wheel (no build).
- `https://docs.aiogram.dev/en/latest/` serves the 4.x docs. The 3.x docs remain reachable.
- The 3.x support dates on the published pages equal `support_dates.py --ga <tag date>`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Switching RTD `latest` at beta | `latest` switches at GA | 18 §1 |
| GA with open P1 issues | J gate | D121 |

## Validation

```bash
# on dev-4.x after the tag
gh workflow run release.yml --ref v4.0.0
gh release view v4.0.0
gh run list --workflow release.yml --limit 1
# on each Tier-1 OS (Linux, macOS, Windows), result recorded in Notes
uv run --isolated --no-project --with aiogram==4.0.0 aiogram info --json
uv run python scripts/support_dates.py --ga <tag date>
curl -fsS https://docs.aiogram.dev/en/latest/ | grep -n "4.0.0"
```

## Workflow notes

- Inputs: all J plans, I-02.
- Last plan of the 4.0 programme.

## Notes

(empty)
