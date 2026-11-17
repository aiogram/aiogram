# J — GA

**Goal.** Turn a feature-complete beta into 4.0.0 GA:
- prove every decision is implemented and tested, not only resolved on paper;
- finish the migration guide;
- resolve beta feedback;
- publish the release notes and the 3.x support dates (D73);
- document release ownership and rollback;
- coordinate the external package releases;
- switch Read the Docs `latest`.

**Exit gate (README D121).** Beta feedback resolved and **no unresolved P1 contract**; release ownership documented,
with rollback restored from the review's §9 J gate; 3.x support dates published. PD-01: the full D121 feature set blocks GA.

**Normative inputs.** [plans README §1](../README.md) (PD-01 to PD-31) → [19](../../research/19-review-resolutions.md)
→ research pages.

## Tasks

| ID | Title | Depends on | Gate-cond. | Size |
|---|---|---|---|---|
| [J-01](J-01-feature-inventory-audit.md) | Feature inventory audit (D/PD/breaking changes/P1 evidence) | C-25, C-27, D-15, D-16, E-21, F-16, G-02, H-20, I-21, I-22 | no | M |
| [J-02](J-02-migration-guide-completion.md) | Migration guide completion | C-26, F-17, G-20, I-10, I-12, I-22 | no | L |
| [J-03](J-03-beta-triage-p1-signoff.md) | Beta triage + P1 sign-off | I-23, J-01, J-05 | no | S (+ beta period) |
| [J-04](J-04-release-notes-3x-support-dates.md) | Release notes + 3.x support dates (`dev-4.x`) | 3x-24, J-01, J-03 | no | S |
| [J-08](J-08-3x-support-banner-dates.md) | 3.x companion: banner, dates, README (`dev-3.x`) | 3x-24, J-04 | no | S |
| [J-05](J-05-release-ownership-runbook-rollback.md) | Release ownership, runbook, rollback / yank | I-01, I-02, I-21 | no | S |
| [J-06](J-06-external-package-releases.md) | External package releases (tracks G-20 / G-21) | G-20, G-21, I-21 | no | S |
| [J-07](J-07-ga-cut-rtd-switch.md) | GA cut + RTD `latest` switch | I-02, J-01, J-02, J-03, J-04, J-05, J-06, J-08 | no | S |

## Order and parallel lanes

1. J-05 can start as soon as I-02 / I-21 exist (it is needed for the J-03 sign-off).
2. After the beta (I-23):
   - J-02 and J-03 run in parallel through the beta period;
   - J-01 starts once I-22 has produced its report.
3. J-06 tracks G-20 / G-21 in parallel.
4. J-04 after the J-01 inventory and the J-03 sign-off; J-08 (`dev-3.x`) right after J-04, before J-07.
5. J-07 last.

## Decide items (proposed defaults, flagged to the owner)

| Item | Plan | Proposed default |
|---|---|---|
| Release manager / backup names | J-05 | owner fills them in |
| External-package release order | J-06 | same day as GA, before the aiogram tag |
| GitHub default branch at GA | J-07 | switch to `dev-4.x`; `dev-3.x` protected until 3.x EOL |
| uk_UA at GA | J-01 (checks I-11) | not GA-blocking |
