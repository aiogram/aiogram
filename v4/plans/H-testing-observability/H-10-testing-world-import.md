# H-10 — Testing World import + packaging

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md) |
| Blocks | [H-11](H-11-generated-toolkit-tables.md), [H-12](H-12-toolkit-model-api-migration.md), [H-14](H-14-delivery-through-runner.md) |
| Gate-conditional | no |
| Decisions | D51, D89, D17, D70 |
| Sources | [14-testing.md §1–3](../../research/14-testing.md), [08-build-release.md §8 extras](../../research/08-build-release.md), PR #1887 (branch `origin/feature/testing`, read-only) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

PR #1887 ("Testing World", last wave #1951) adds `aiogram.test`: 17 006 lines in 20 modules, about 1 880 tests in
`tests/test_testing/`, and a 3 580-line `docs/dispatcher/testing.rst`. Its merge base with `dev-3.x` is `bea6716a`,
44 commits behind. The branch also carries about 22k lines of OpenSpec files, `.claude/commands/opsx/**`, and
squashed `dev-3.x` work.

D51 ships the toolkit in the core wheel with an **opt-in** plugin (no `pytest11` entry point). D89 drops OpenSpec.
This task lands the toolkit on `dev-4.x` **as it is**, running against the 3.x-derived types A-01 put on `dev-4.x`.
The model-API port happens later (H-12, gate-conditional), so this part doesn't wait for B.

## Scope

**In:**
- Bring over from `origin/feature/testing` **only**:
  - `aiogram/test/**` (the 20 modules: `environment`, `blueprint`, `world`, `actors`, `modeling`, `markup`,
    `synthesis`, `rejections`, `errors`, `flood`, `overrides`, `plugin`, `session`, `mounting`, `calls`,
    `defaults`, `rich`, `routing`, `waiting`, `__init__`);
  - `tests/test_testing/**`;
  - `docs/dispatcher/testing.rst`;
  - the PR's changelog fragment.

  Use a path-limited checkout from the branch. Do not merge it.
- **Not** brought over:
  - `openspec/**`, `.claude/commands/opsx/**` (D89);
  - the squashed `dev-3.x` changes (`docs/api/types/*.rst`, `docs/migration_2_to_3.rst`, …);
  - the `[project.entry-points.pytest11]` table;
  - `addopts = "-p no:aiogram"`.
- Packaging:
  - the `test` extra is `pytest>=8`, **lower bound only** (D70; the PR has `<10`);
  - aiogram's own suite enables the plugin with `pytest_plugins = ["aiogram.test.plugin"]` in the **root**
    `tests/conftest.py` (pytest rejects `pytest_plugins` in non-root conftests);
  - check that `aiogram/test/**` is measured by coverage.
- Fix drift against `dev-4.x` HEAD (Bot API types added since `bea6716a`) only as far as needed for the imported
  tests to pass. New methods without a fake model get an explicit `synthesize` mark.
- Docs: users enable the plugin with `-p aiogram.test.plugin` or `pytest_plugins`.

**Out:**
- The model-API migration (H-12).
- Generated tables (H-11).
- The binding rewrite (H-13).
- Runner delivery (H-14).
- The docs port to the 4.0 structure (H-18).
- Final extras layout (I-07). This plan adds `test` in the current `pyproject.toml` shape.

## Checklist

- [ ] Path-limited import of the files listed above, with OpenSpec and the squashed dev-3.x changes excluded.
- [ ] `pyproject.toml`: no `pytest11` entry point, no `-p no:aiogram`, `test = ["pytest>=8"]`.
- [ ] Root `tests/conftest.py` loads the plugin. Coverage report shows `aiogram/test/*` measured.
- [ ] Make the imported suite green against `dev-4.x` HEAD (drift fixes only, listed in the PR body).
- [ ] **Decide #1887's shipping status in 3.x** (proposed default: #1887 does **not** merge into `dev-3.x`; the
      toolkit first ships in 4.0, so the opt-in plugin is not a break). If the owner ships it in 3.x with the
      entry point, this plan adds a migration-registry entry (PD-13, `removal-4.0`: "the `aiogram` pytest plugin is
      no longer auto-loaded; add `-p aiogram.test.plugin`") and a README breaking-change item request to A-02.
      Record the decision in *Notes* and flag it to the owner.
- [ ] Note in the PR body that PR #1887 is superseded on `dev-4.x` by this import.
- [ ] Changelog fragment (new `aiogram.test` toolkit, opt-in plugin).

## Acceptance criteria

- `git diff --stat` of the PR touches only `aiogram/test/**`, `tests/test_testing/**`, `tests/conftest.py`,
  `docs/dispatcher/testing.rst`, `pyproject.toml`, `uv.lock`, `CHANGES/*`, plus drift fixes listed in the PR body.
- No `openspec/` directory and no `pytest11` entry point on `dev-4.x`.
- `uv run pytest tests` passes, including about 1 880 toolkit tests. Coverage stays at 100% with `aiogram/test/**`
  measured.
- A fresh project with `aiogram[test]` installed and no `-p aiogram.test.plugin` does **not** load the plugin
  (`pytest --trace-config` shows it absent).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Separate `aiogram-test` distribution | Its generated parts must match the installed API | D51, D17 |
| `pytest11` auto-loaded entry point | Imposes fixtures and hooks on every aiogram user's test session; forced the `-p no:aiogram` workaround | D51 |
| Keeping OpenSpec files in the tree | `docs/dispatcher/testing.rst` is the specification; OpenSpec stays in branch history | D89 |
| Merging the branch | It carries squashed dev-3.x work and OpenSpec | D89 |

## Validation

```bash
uv sync --locked --all-extras --group dev --group test
make dev            # once B-01 has landed
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Starts right after A-01, in parallel with everything else. Not gate-conditional, because it runs against the
  3.x-derived types still in `aiogram.types` (PD-03).
- Outputs: the toolkit tree that H-11…H-18 change.
- I-07 later moves `test` into the final extras list without changing its meaning.

## Notes
