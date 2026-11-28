# I-21 — Fresh-machine install rehearsal across Tier 1

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-01](I-01-packaging-hardening.md), [I-02](I-02-tier1-wheel-matrix-release.md), [I-03](I-03-free-threaded-wheels-ci.md), [I-04](I-04-installed-wheel-typing-stubtest.md), [I-07](I-07-dependencies-extras-restructure.md), [G-15](../G-features/G-15-cli-core.md) |
| Blocks | [I-23](I-23-beta-pre-release.md), [J-01](../J-ga/J-01-feature-inventory-audit.md), [J-05](../J-ga/J-05-release-ownership-runbook-rollback.md), [J-06](../J-ga/J-06-external-package-releases.md) |
| Gate-conditional | no |
| Decisions | D17, D119, PD-27, R25, D76 (`aiogram info`) |
| Sources | [08-build-release.md §4](../../research/08-build-release.md), [19 D119, R25](../../research/19-review-resolutions.md), [17-cli.md §1 `aiogram info`](../../research/17-cli.md), [README milestone I](../../research/README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Milestone I's exit gate is "fresh-machine install and 3→4 migration rehearsals across Tier 1". I-02 tests each wheel in
a venv on a runner that already has Rust, a compiler and caches. A user's machine has none of those. R25 asks for tests
of the installed wheels, the sdist offline build and the fallback behaviour on unsupported systems. PD-27 bounds what
counts as a failure: our wheels and our suite only.

## Scope

**In:**
- **A rehearsal workflow** (`workflow_dispatch` + on release candidates) per Tier-1 platform × interpreter:
  - a clean container or VM image **without** Rust or a C compiler (Linux: `python:<v>-slim` and an Alpine musl
    image; macOS and Windows: hosted runners with `rustc` / `cargo` removed from PATH, asserted);
  - `pip install aiogram==<rc>` from a local index serving only the I-02 artifacts;
  - `python -c "import aiogram"`;
  - `aiogram info --json` (G-15): asserts the wheel tag, free-threaded / GIL state and the core build version
    (I-01 equality);
  - run the `echo_bot.py` smoke through the toolkit.
- **Extras.** Per extra: `pip install aiogram[<extra>]==<rc>` + an import smoke. Free-threaded cells follow the I-03
  table (missing third-party wheels are documented, not failures, PD-27).
- **sdist.** Install with Rust present and cargo offline (reuse I-01's job). Install **without** Rust on a non-Tier-1
  target (e.g. `linux/riscv64` under QEMU): assert the failure message matches the I-01 decision.
- **Upgrade from 3.x.** In a venv with aiogram 3.x, `aiogram-cli` 1.1 and `aiogram_i18n` installed, `pip install -U
  aiogram==<rc>`: record resolver behaviour (aiogram-cli pins `aiogram<4`) and the console-script ownership. This is
  input to J-06 and G-21.
- **Results matrix** committed as `ci/install-rehearsal.md`, generated from the run.

**Out:**
- Migration rehearsal (I-22).
- Fixing third-party wheel gaps.

## Checklist

- [ ] Workflow with the platform × interpreter matrix from I-02's Tier-1 list.
- [ ] Local index step (`python -m http.server` over a `simple/` layout, or `pip install --no-index --find-links`).
- [ ] Assert "no Rust / no compiler" at job start.
- [ ] Extras loop. Treat a missing third-party wheel cell as "documented" per PD-27 and the I-03 table.
- [ ] Upgrade-from-3.x scenario. Write the findings into Notes and hand them to J-06 / G-21.
- [ ] Generate the results matrix file.
- [ ] Tests: the workflow is the test. Add a unit test for the results-matrix generator script (100% coverage).
- [ ] No changelog fragment (`skip news`).

## Acceptance criteria

- Every Tier-1 cell is ✔ for import, `aiogram info` and the echo smoke on a machine without Rust or a compiler.
- The extras cells match I-03's published ft table. No undocumented ✖.
- The non-Tier-1 sdist-without-Rust cell shows the documented message.
- The upgrade scenario's outcome is recorded with concrete pip output.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Counting I-02's per-wheel test as the rehearsal | Runner has Rust and caches; not a fresh machine | README milestone I, R25 |
| Blocking on third-party ft wheels | Tier 1 = ours | PD-27 |

## Validation

```bash
gh workflow run install-rehearsal.yml -f version=<rc>
uv run pytest tests/ci -q
make lint-workflows
```

## Workflow notes

- Inputs: I-01 (message, version equality), I-02 (artifacts), I-03 (ft table), I-04 (typing passes), I-07 (extras),
  G-15 (`aiogram info`).
- Outputs:
  - results matrix (J-01, J-05);
  - upgrade findings (J-06, G-21).
- Runs again for every release candidate before J-07.

## Notes

(empty)
