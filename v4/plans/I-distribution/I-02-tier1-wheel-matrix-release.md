# I-02 — Tier-1 wheel matrix and release workflow

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-01](I-01-packaging-hardening.md), [I-05](I-05-pr-ci-structure-caching-coverage.md), [C-18](../C-butcher/C-18-rust-type-emitter.md), [C-02](../C-butcher/C-02-fetch-provenance.md) |
| Blocks | [I-03](I-03-free-threaded-wheels-ci.md), [I-21](I-21-fresh-machine-install-rehearsal.md), [I-23](I-23-beta-pre-release.md), [J-05](../J-ga/J-05-release-ownership-runbook-rollback.md), [J-07](../J-ga/J-07-ga-cut-rtd-switch.md) |
| Gate-conditional | no |
| Decisions | D17, D119, PD-35, PD-27, R25 |
| Sources | [08-build-release.md §3–5](../../research/08-build-release.md), [19 D119, R25](../../research/19-review-resolutions.md), [codex-review R25](../../research/codex-review.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D119 makes platform support release-blocking. Today's `.github/workflows/pypi-release.yml` builds one pure-Python
wheel and one sdist with `uv build`, then publishes through trusted publishing. 4.0 needs about 60–90 compiled wheels per
release (08 §4), about 10 minutes each (08 §3). A missing Tier-1 wheel must stop the release, while a failing best-effort
wheel must not.

PD-27 defines Tier 1 as "**our** wheels build and **our** suite passes". Missing third-party free-threaded wheels (e.g.
frozenlist has no cp315t wheel, cryptography is 314t-only, 07 §4) are documented, not release-blocking.

## Scope

**In:**
- **Tier 1, release-blocking:** cp311, cp312, cp313, cp314, cp315, cp314t, cp315t ×
  manylinux x86_64/aarch64, musllinux x86_64/aarch64, macOS arm64/x86_64, Windows x64.
- **Best-effort, non-blocking:** Windows arm64, manylinux i686/armv7l/ppc64le/s390x.
- Always one sdist.
- Built with `PyO3/maturin-action` (start from `maturin generate-ci github`), rust-cache keyed with
  `PYO3_ENVIRONMENT_SIGNATURE` (13 B12).
- **Per-wheel test:** each Tier-1 wheel is installed into a clean venv and the test suite runs against it
  (`python -P`, from outside the checkout). Emulated aarch64 may run a smoke subset (decide item).
- **Publishing:** a `publish` job needs **all** Tier-1 jobs plus the sdist. It uploads them with trusted
  publishing and build attestations (`pypa/gh-action-pypi-publish`, `attestations: true`). A separate
  `publish-best-effort` job uploads whatever best-effort wheels succeeded, after Tier 1 (PyPI allows adding files to an
  existing release).
- A scheduled weekly **release dry run** (build everything, publish nothing) so breakage shows up before a tag.
- zizmor-clean workflows (`make lint-workflows`).

**Out:**
- Free-threaded test specifics: `PYTHON_GIL=0`, the GIL check, extras combos (I-03).
- PR CI (I-05).
- Fresh-machine install rehearsal (I-21).
- Rollback and yank policy (J-05).

## Checklist

- [ ] Replace `pypi-release.yml` on `dev-4.x` with the matrix workflow. Keep the 3.x file untouched on `dev-3.x`.
- [ ] Encode tiers in one place: a matrix include list with `tier: 1 | best-effort`. Best-effort jobs use
      `continue-on-error: true` and are not in `publish.needs`.
- [ ] Per-wheel test job: install the artifact, run `pytest` from a temp dir against the installed package. Port
      the version smoke check from I-01.
- [ ] Linux: manylinux_2_28 for x86_64/aarch64 and musllinux_1_2. Prefer native aarch64 runners where available.
- [ ] macOS: separate arm64 and x86_64 builds, not universal2 (decide only if size or runners force it).
- [ ] `twine check --strict` on all artifacts (as in 3.x).
- [ ] Attestations and trusted publishing. No API tokens in the repo.
- [ ] Scheduled dry run (`schedule:` weekly + `workflow_dispatch`). On failure it opens an issue.
- [ ] **Decide the release CI cost** (08 §5/§4: about 60–90 wheels × about 10 min). Proposed default: the full matrix runs only on
      tags and the weekly dry run. Tier-1 wheels are cached by commit (13 B12) so a re-run after a flaky job doesn't
      rebuild everything. Emulated (QEMU) targets run a smoke subset (`import aiogram`, decode one corpus update,
      `tests/test_api`) rather than the full suite. Record the measured wall-clock and runner-minutes in Notes and flag
      them to the owner.
- [ ] Document the tier table in the Install docs page stub. I-10 owns the page; this plan provides the text.
- [ ] Tests: workflow logic lives in YAML, so verify it with a `workflow_dispatch` dry run that produces the full artifact
      set, and with `make lint-workflows`.
- [ ] Changelog fragment `CHANGES/<id>.misc.rst` (wheel platforms list). No registry entry (packaging break covered
      by I-01).

## Acceptance criteria

- One dry run produces every Tier-1 wheel (7 interpreters × 7 platforms = 49) plus the sdist. Each Tier-1 wheel's
  suite or smoke job is green.
- Removing one Tier-1 job's artifact (e.g. a forced failure via an input flag) makes `publish` skip. A failing
  best-effort job doesn't.
- `make lint-workflows` (with `GH_TOKEN=$(gh auth token)` for online audits) passes.
- The measured total runner-minutes and wall-clock are recorded in Notes.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| abi3 / abi3t wheels in 4.0 | Can't load on ft builds; per-version speedups kept; revisit when the floor reaches 3.15 (PEP 803) | 08 §4, 13 B16 |
| PyPy wheels (unsupported in 4.x) | Owner decision | PD-35 |
| Windows arm64, i686 etc. release-blocking | Best-effort tier | D119 |
| Blocking on third-party ft wheels | Tier 1 is our wheels and our suite | PD-27 |
| Fat LTO in release profile | 3× build time, OOM on 16 GB, ≈2% gain | 08 §3, 13 B4 |

## Validation

```bash
make lint-workflows
GH_TOKEN=$(gh auth token) make lint-workflows
gh workflow run release.yml -f dry_run=true   # on a fork or the dev-4.x branch; check artifacts
```

## Workflow notes

- Inputs:
  - I-01 (wheel layout, version source, smoke step);
  - I-05 (cache keys);
  - C-18 (the full generated crate, needed to measure real build times).
- Outputs:
  - artifacts and the publish job, used by I-03, I-21, I-23, J-05 and J-07;
  - measured build cost, used by I-05 and I-06.

## Notes

(empty)
