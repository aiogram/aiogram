# H-10 — Testing World import + packaging

| Field | Value |
|---|---|
| Status | `done` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md) |
| Blocks | [H-11](H-11-generated-toolkit-tables.md), [H-12](H-12-toolkit-model-api-migration.md), [H-14](H-14-delivery-through-runner.md) |
| Gate-conditional | no |
| Decisions | D51, D89, D17, D70 |
| Sources | [14-testing.md §1–3](../../research/14-testing.md), [08-build-release.md §8 extras](../../research/08-build-release.md), PR #1887 (merged into `dev-3.x` as `52faf0ff`), TW-188 in `design/testing-toolkit/decisions.md` |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

PR #1887 ("Testing World") adds `aiogram.test`: the toolkit package, about 2 900 tests in `tests/test_testing/`,
`docs/dispatcher/testing.rst` and the design notes in `design/testing-toolkit/`. It merged into `dev-3.x` as
`52faf0ff` without OpenSpec (D89) and shipped in 3.33.0.

D51 ships the toolkit in the core wheel. Its pytest plugin loads on its own through a lazy `pytest11` entry-point
shim (TW-188; D51 as revised by the owner on 2026-11-19). `dev-4.x` gets the toolkit **as it is** through the regular
`dev-3.x` → `dev-4.x` sync, running against the 3.x-derived types A-01 put on `dev-4.x`. The model-API port happens
later (H-12, gate-conditional), so this part doesn't wait for B. This plan holds only what is specific to 4.x.

## Scope

**In:**
- Sync: `dev-4.x` carries #1887 (`52faf0ff`) through the `dev-3.x` → `dev-4.x` sync (the fast-forward to 3.33.0,
  `658bb431`). There is no separate import or cherry-pick, so every toolkit fix lives in one place and later syncs
  bring 3.x fixes over. The sync brings, unchanged:
  - `aiogram/test/**`, including the shim `aiogram/test/_autoload.py`;
  - `tests/test_testing/**`, `docs/dispatcher/testing.rst`, `design/testing-toolkit/**`;
  - `[project.entry-points.pytest11] aiogram = "aiogram.test._autoload"` and `addopts = "-p no:aiogram"` (the suite
    blocks the entry point so coverage starts first);
  - `pytest_plugins = ["aiogram.test.plugin"]` in the **root** `tests/conftest.py`.
- Packaging, specific to 4.x: the `test` extra is `pytest>=8`, **lower bound only** (D70; 3.x has `<10`), with
  `uv.lock` regenerated and a changelog fragment for it.
- Plan docs: the H story README and H-18 describe the shim, not an opt-in plugin.

**Out:**
- Toolkit code, test and docs fixes. They land on `dev-3.x` and come over with the next sync.
- D51's text in `v4/research/` (A-02).
- The model-API migration (H-12).
- Generated tables (H-11).
- The binding rewrite (H-13).
- Runner delivery (H-14).
- The docs port to the 4.0 structure (H-18).
- Final extras layout (I-07). This plan changes `test` in the current `pyproject.toml` shape.

## Checklist

- [x] `dev-4.x` carries `52faf0ff` through the `dev-3.x` → `dev-4.x` sync (fast-forward to `658bb431`, 3.33.0).
- [x] `pyproject.toml`: `test = ["pytest>=8"]`, `uv.lock` regenerated. The `pytest11` shim and `-p no:aiogram` stay
      as 3.x has them.
- [x] Root `tests/conftest.py` loads the plugin (from 3.x). Coverage report shows `aiogram/test/*` measured.
- [x] The suite is green on `dev-4.x`.
- [x] **Decide #1887's shipping status in 3.x** (proposed default: #1887 does **not** merge into `dev-3.x`; the
      toolkit first ships in 4.0, so the opt-in plugin is not a break). If the owner ships it in 3.x with the
      entry point, this plan adds a migration-registry entry (PD-13, `removal-4.0`: "the `aiogram` pytest plugin is
      no longer auto-loaded; add `-p aiogram.test.plugin`") and a README breaking-change item request to A-02.
      Record the decision in *Notes* and flag it to the owner.
      *Answered 2026-11-19: shipped in 3.33.0 with the entry-point shim, which 4.x keeps; no break, no PD-13 entry,
      no README request.*
- [x] No changelog fragment: the PR carries `skip news`, I-07 writes the 4.0 extras fragment, and the toolkit's own
      fragment shipped in 3.33.0.

## Acceptance criteria

- `git diff --stat origin/dev-4.x` of the PR touches only `pyproject.toml`, `uv.lock` and `v4/plans/**`.
- `origin/dev-4.x` contains `52faf0ff`. No `openspec/` directory.
- `uv run pytest tests` passes, including about 2 900 toolkit tests. Coverage stays at 100% with `aiogram/test/**`
  measured.
- A fresh project with `aiogram[test]` installed loads the plugin with no setup; `-p no:aiogram` turns it off; an
  explicit `-p aiogram.test.plugin` or `pytest_plugins` still works and loads it once
  (`tests/test_testing/test_plugin.py::TestPluginDiscovery`).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Separate `aiogram-test` distribution | Its generated parts must match the installed API | D51, D17 |
| Opt-in plugin, no `pytest11` entry point (D51 before 2026-11-19) | Every user needs a setup step, and `fixture 'bot_env' not found` does not say which; it saves about 1.3 s of `import aiogram` only for projects whose tests never import aiogram, which are rare | D51 revised, TW-188 |
| `pytest11` entry point pointing straight at `aiogram.test.plugin` | An explicit `-p aiogram.test.plugin` or `pytest_plugins` then fails with "Plugin already registered under a different name" | TW-188 |
| Path-limited import from `feature/testing` into `dev-4.x` (the first pass of #2018) | Two copies of the toolkit, so every fix had to land twice; superseded once #1887 merged into `dev-3.x` | Owner, 2026-11-19 |
| Keeping OpenSpec files in the tree | `docs/dispatcher/testing.rst` is the specification; OpenSpec stays in branch history | D89 |
| Merging the `feature/testing` branch | It carries squashed dev-3.x work and OpenSpec | D89 |

## Validation

```bash
uv sync --locked --all-extras --group dev --group test
make dev            # once B-01 has landed
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Starts once #1887 is on `dev-3.x` and the next sync has run, in parallel with everything else. Not gate-conditional, because it runs against the
  3.x-derived types still in `aiogram.types` (PD-03).
- Outputs: the toolkit tree that H-11…H-18 change.
- I-07 later moves `test` into the final extras list without changing its meaning.

## Notes

- 2026-11-18 — first pass (#2018): path-limited import from `origin/feature/testing@9134b74e` with an opt-in
  plugin, as this plan specifies. The drift fixes (Bot API 10.4 `widget_query` / `shared_widget_query` triggers,
  ruff UP017/UP035/UP042) and three review fixes in the imported code were folded back into #1887.
- 2026-11-19 — **the shipping-status decision is reversed.** The owner merged #1887 into `dev-3.x` (`52faf0ff`,
  ships in 3.x) with the plugin auto-loaded through a lazy `pytest11` entry-point shim (`aiogram/test/_autoload.py`,
  TW-188 in `design/testing-toolkit/decisions.md`), and revised D51 for 4.x to match. So the opt-in items in
  *Scope*, *Checklist*, *Acceptance criteria* and the `pytest11` row of *Rejected alternatives* are superseded:
  `dev-4.x` keeps the entry point and `addopts = "-p no:aiogram"`; no plugin-loading break, no PD-13
  `removal-4.0` entry, no README request to A-02.
- 2026-11-19 — the toolkit reaches `dev-4.x` through the regular `dev-3.x` → `dev-4.x` sync (owner's choice: one
  sync after 3.33.0), not through an import. This plan keeps only the 4.x-specific part: the `test` extra is
  `pytest>=8` without the `<10` cap (D70).
- D51's text in `v4/research/` still says opt-in; that page belongs to A-02.
- 2026-11-20 — re-plan (owner): *Motivation*, *Scope*, *Checklist*, *Acceptance criteria* and *Rejected
  alternatives* are rewritten to the real mechanism (the `dev-3.x` sync and the TW-188 shim). The opt-in text the
  2026-11-19 notes call superseded is in this file's history.
- 2026-11-20 — owner: no changelog fragment for the `test` extra cap (too small for the 4.0 notes; I-07 writes the
  extras fragment). #2018 carries `skip news`.
