# J-03 — Beta feedback triage and P1 sign-off

| Field | Value |
|---|---|
| Status | `todo` |
| Story | J — GA |
| Target branch | `dev-4.x` |
| Depends on | [I-23](../I-distribution/I-23-beta-pre-release.md), [J-01](J-01-feature-inventory-audit.md), [J-05](J-05-release-ownership-runbook-rollback.md) |
| Blocks | [J-04](J-04-release-notes-3x-support-dates.md), [J-07](J-07-ga-cut-rtd-switch.md) |
| Gate-conditional | no |
| Decisions | D121, PD-01 |
| Sources | [README milestone J](../../research/README.md), [codex-review.md §3, §9](../../research/codex-review.md), [19 D121](../../research/19-review-resolutions.md) |
| Size | S (≤1 day) of setup; the triage itself runs through the beta period |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The J gate reads "beta feedback resolved; **no unresolved P1 contract**". The review defines P1 as "resolve before
implementing the affected public contract or relying on the safety claim" (codex-review §3). Beta reports need the same
classification, so "resolved" is checkable rather than a feeling.

## Scope

**In:**
- **A P1 definition for beta issues.** A beta issue is P1 if it:
  - breaks a documented public contract (a decision id in the README / 19 / PD table);
  - makes a Tier-1 install fail (PD-27 scope);
  - leaks a token;
  - loses or duplicates updates beyond the documented best-effort delivery (R13);
  - is a migration-tool rewrite that produces wrong code silently (a definite-class false positive).
  Everything else is P2/P3.
- Labels `4.0-beta`, `P1` / `P2` / `P3`, and a triage cadence (weekly) recorded in this plan's Notes.
- **Triage log** `v4/plans/J-ga/beta-triage.md`: issue, class, decision id, owning plan, resolution PR. Generated from
  `gh issue list --label 4.0-beta --json` plus manual columns.
- **Exit sign-off:**
  - zero open P1;
  - every P2 has an owner and a target (4.0 or 4.0.x);
  - the J-01 P1-contract table is all green;
  - signed off by the release owner (J-05).
- Further betas or release candidates (`4.0.0b2`, `rc1`) through the I-23 / I-02 flow when fixes land.

**Out:**
- Fixing issues (the owning story).
- GA cut (J-07).

## Checklist

- [ ] Write the P1 definition into the issue template (I-23) and the Contributing page.
- [ ] Script `scripts/beta_triage.py` producing `beta-triage.md` from `gh`. Use `rtk proxy gh` / a temp file for long
      bodies if run through rtk.
- [ ] Weekly triage notes in Notes (date, opened / closed P1).
- [ ] Re-run I-21 and I-22 on each new beta / rc.
- [ ] Sign-off line: "No open P1 as of <date>, release owner <name>".
- [ ] Tests for the triage script (100% coverage).
- [ ] No changelog fragment.

## Acceptance criteria

- `beta-triage.md` lists every `4.0-beta` issue, and zero P1 are open at sign-off.
- The sign-off line is filled in by the J-05 release owner.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| GA after a fixed calendar beta period regardless of P1 | Gate is "no unresolved P1" | D121 |
| Moving P1 features to 4.1 to close them | Full feature set blocks GA | PD-01 |

## Validation

```bash
uv run python scripts/beta_triage.py --check   # exits non-zero while any P1 is open
uv run pytest tests/ci -q
```

## Workflow notes

- Inputs: I-23 (beta, template, label), J-01 (P1-contract table).
- Outputs: sign-off used by J-04 and J-07.

## Notes

(empty)
