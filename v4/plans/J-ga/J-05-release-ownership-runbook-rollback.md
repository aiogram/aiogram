# J-05 — Release ownership, runbook and rollback / yank policy

| Field | Value |
|---|---|
| Status | `todo` |
| Story | J — GA |
| Target branch | `dev-4.x` |
| Depends on | [I-01](../I-distribution/I-01-packaging-hardening.md), [I-02](../I-distribution/I-02-tier1-wheel-matrix-release.md), [I-21](../I-distribution/I-21-fresh-machine-install-rehearsal.md) |
| Blocks | [J-03](J-03-beta-triage-p1-signoff.md), [J-07](J-07-ga-cut-rtd-switch.md) |
| Gate-conditional | no |
| Decisions | D119, PD-27, D121, D73 |
| Sources | [19 D119](../../research/19-review-resolutions.md), [08-build-release.md §4–5](../../research/08-build-release.md), [codex-review.md §9 (J gate: "rollback and release ownership documented")](../../research/codex-review.md), [README milestone J](../../research/README.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The README J row requires "release ownership documented". The review's J gate (codex-review §9) also lists
**rollback**, which the README row dropped. It is restored here.

A compiled release of about 60–90 wheels can go wrong in ways a pure-Python release can't:
- a Tier-1 wheel that imports but crashes;
- a broken best-effort wheel uploaded after Tier 1;
- a version-source drift between `__meta__.py` and the Cargo version.

PyPI files are immutable: a broken file can only be **yanked** (PEP 592) and superseded, never replaced.

The 3.x process lives in the `aiogram-release` skill and the Makefile `bump` / `towncrier-build` / `prepare-release` /
`release` targets. It assumes hatchling and one pure-Python wheel.

## Scope

**In:**
- **Ownership.** A named release manager and a backup for 4.0.0 and the 4.0.x line, plus a named owner for the 3.x
  maintenance line until its EOL (D73). Recorded in `RELEASING.md` (new, `dev-4.x`) and linked from Contributing.
- **Runbook `RELEASING.md`:**
  - **pre-flight:** J-01 inventory green; J-03 no open P1; I-21 install rehearsal on the rc artifacts; I-22 rehearsal
    current; version equality check (I-01);
  - **cut:** bump, then towncrier, then tag, then the I-02 workflow. `publish` waits for all Tier-1 jobs;
    best-effort uploads follow;
  - **post-release:** install smoke from PyPI on each Tier-1 OS (`pip install aiogram==X` in a clean venv, `aiogram
    info`), RTD check, announcement.
- **Rollback / yank policy:**
  - **Broken Tier-1 file(s):** yank the whole release (`pypi` web UI / API; yanking is per release). Publish `X.Y.Z+1`
    with the fix. Never delete files, because PyPI forbids re-uploading the same filename.
  - **Broken best-effort file only:** don't yank the release. Publish a post-release fix in the next patch, document
    the known issue on the release page, and tell best-effort users to pin the previous version (PD-27: best-effort
    never blocks).
  - **Partial upload** (publish job failed midway): re-run the publish job. Trusted publishing skips existing files
    (`skip-existing: true` on re-runs only). If a Tier-1 file is missing after the re-run, yank and re-release.
  - **Security issue in a release:** coordinate via SECURITY.md, yank, then patch release. The 3.x line follows the
    same policy during its security-only phase.
  - **Who may yank:** the release manager or backup. Record every yank in `RELEASING.md`'s log.
- **Update the `aiogram-release` skill / Makefile targets** for the maturin build and the version source (I-01).

**Out:**
- The workflow implementation (I-02).
- External packages (J-06).

## Checklist

- [ ] `RELEASING.md` with ownership, runbook, rollback / yank policy and a yank log.
- [ ] Owner names filled in by the owner. This plan leaves `<name>` placeholders and flags them.
- [ ] Port `make prepare-release` / `make release` to `dev-4.x` (maturin, tag-triggered workflow).
- [ ] Update the `aiogram-release` skill (`.claude/skills/aiogram-release`) for `dev-4.x` differences, or add a 4.x
      variant if that skill must stay 3.x-only. Record which in Notes.
- [ ] Rehearse a yank on TestPyPI with a throwaway pre-release version and record the steps.
- [ ] No tests beyond the TestPyPI rehearsal. No changelog fragment.

## Acceptance criteria

- `RELEASING.md` names a release manager and a backup for 4.0 (the owner fills them in) and covers every rollback case
  above.
- The TestPyPI rehearsal shows: a yanked release isn't picked by `pip install aiogram` but is by `==X.Y.Z`. The re-run
  publish path is exercised.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Deleting broken files from PyPI | Filename can never be re-used; yank instead (PEP 592) | (this plan) |
| Yanking a release for a best-effort-only failure | Best-effort never blocks | D119, PD-27 |
| Undocumented ownership | J gate requires it | D121 |

## Validation

```bash
make -n prepare-release && make -n release
# TestPyPI yank rehearsal, steps recorded in Notes
```

## Workflow notes

- Inputs: I-01 (version source), I-02 (publish job), I-21 (rehearsal).
- Outputs: the runbook used by J-03 sign-off and J-07.

## Notes

(empty)
