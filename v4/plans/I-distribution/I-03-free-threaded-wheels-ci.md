# I-03 — Free-threaded wheels and CI

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-02](I-02-tier1-wheel-matrix-release.md) |
| Blocks | [I-21](I-21-fresh-machine-install-rehearsal.md), [F-16](../F-fsm/F-16-race-suite-314t.md) |
| Gate-conditional | no |
| Decisions | D8, D119, PD-27, R25 |
| Sources | [07-free-threading.md §2, §4–5](../../research/07-free-threading.md), [08-build-release.md §4–5](../../research/08-build-release.md), [codex-review R25](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Free-threaded CPython 3.14t/3.15t is first-class (D8) and Tier 1 (D119). A free-threaded wheel only stays free-threaded if:
- the extension declares support, so importing it doesn't silently re-enable the GIL;
- every enabled extra keeps working without the GIL.

R25 points out that pure-Python dependencies are not automatically thread-safe, and asks for the supported combinations
to be published. 07 §4 lists the dependency readiness as of 2026-11:
- frozenlist has no 315t wheel;
- cryptography ships 314t only;
- orjson has no ft wheels.

## Scope

**In:**
- Test jobs on the **installed** cp314t/cp315t wheels (Linux + macOS) running the full suite with `PYTHON_GIL=0`.
- A conftest guard that fails when `sys._is_gil_enabled()` is true after `import aiogram` and after importing each
  extra's integration module.
- An **extras × ft matrix** job: install `aiogram[<extra>]` on 3.14t and 3.15t, import its integration module, run that
  extra's tests.
- The published support table (decide item), with missing third-party wheels documented per PD-27.
- An optional scheduled ThreadSanitizer job for the Rust core (`RUSTFLAGS=-Zsanitizer=thread`, nightly toolchain).

**Out:**
- The race tests themselves: F-16 (FSM, 3.14t race suite), B-11 (cache/GC/ft), E-19 (multi-Runner), E-22 (sharding).
  This plan only makes sure they run on ft wheels.
- Wheel building (I-02).

## Checklist

- [ ] Add `tests/conftest.py` hook: when `sysconfig.get_config_var("Py_GIL_DISABLED")` is set, assert
      `not sys._is_gil_enabled()` at session start and after the import sweep. Skip on GIL builds.
- [ ] Workflow jobs `ft-tests` (3.14t, 3.15t × ubuntu, macOS), installing the I-02 artifact, `PYTHON_GIL=0`.
- [ ] Extras matrix job over `fast`, `redis`, `mongo`, `proxy`, `signature`, `i18n`, `fluent-runtime`,
      `fluent-compiler`, `otel`, `test`, `migrate`, `reload` (the D67–D70 list, 08 §8).
- [ ] **Decide the published ft extras combinations** (proposed default: publish a table in the Install docs, with
      columns extra × {3.14t, 3.15t} and cells ✔ tested / ⚠ installs but a dependency re-enables the GIL / ✖ no wheel.
      An extra failing because of a third-party wheel is marked, not fixed, per PD-27. orjson is never recommended for ft
      builds). Record the first measured table in Notes and flag it to the owner.
- [ ] Check that `aiogram._core` is built without `gil_used = true` (07 §2). A test imports it under
      `-X gil=0` and asserts the GIL stays off.
- [ ] Optional nightly TSan job (scheduled, non-blocking).
- [ ] Tests (100% coverage of the conftest helper logic).
- [ ] Changelog fragment `CHANGES/<id>.feature.rst` ("free-threaded wheels for 3.14t/3.15t"). No registry entry.

## Acceptance criteria

- The ft-tests jobs pass on both ft interpreters with `PYTHON_GIL=0`. A deliberately GIL-requiring test module
  (temporary fixture in the PR) makes the guard fail.
- The extras table exists with every cell filled from a CI run.
- No Tier-1 job is red only because of a missing third-party ft wheel. Such cells are documented instead (PD-27).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| 3.13t support | PyO3 0.29 dropped it; pydantic-core ships no cp313t | 07 intro |
| Blocking a release on a third-party ft wheel | Tier 1 = our wheels and our suite | PD-27 |
| abi3t wheels | Later, when the floor reaches 3.15 | 08 §4 |

## Validation

```bash
make dev && uv run pytest tests                     # GIL build
PYTHON_GIL=0 uv run --python 3.14t pytest tests     # ft build, from the installed wheel in CI
cargo clippy --all-targets -- -D warnings && cargo test
make lint-workflows
```

## Workflow notes

- Input: I-02 artifacts.
- Outputs: the ft support table (I-10 Install page, I-21 rehearsal).
- Runs F-16, B-11, E-19 and E-22 suites as they land, so ordering doesn't matter.

## Notes

(empty)
