# AGENTS.md

This file defines how coding agents should contribute to `aiogram` on `dev-3.x`.

## Scope and defaults

- Base branch: `dev-3.x`
- Python: `>=3.11`
- Main tooling: `uv`, `ruff`, `mypy`, `pytest`, `towncrier`, `butcher`
- Keep diffs focused; avoid unrelated refactors/reformatting.
- Sync `dev-3.x` into a long-lived feature branch with a real merge, never a squash: a
  squash drops the ancestry, and the next sync then conflicts on everything since. To
  repair a lost base, run `git merge-tree --write-tree --merge-base=<real base> HEAD origin/dev-3.x`,
  then `git commit-tree -S <printed tree> -p HEAD -p origin/dev-3.x -m <message>`. `commit-tree` ignores
  `commit.gpgsign`, so always pass `-S`.

## Setup

```bash
uv sync --locked --all-extras --group dev --group test
uv run pre-commit install
```

Note: `uv run pre-commit install` writes hooks to the shared repository `.git/hooks`
(common for all worktrees), not only for the current worktree.

`orca.yaml` runs the same `uv sync` as the setup hook for new worktrees opened in [Orca](https://onorca.dev); it is excluded from the sdist.

## Codebase Navigation

Use **Serena MCP** for all codebase navigation tasks. Serena provides semantic, symbol-aware tools that are more efficient than raw file reads:

- `get_symbols_overview` — list classes/methods in a file without reading the full body
- `find_symbol` — locate a specific class, method, or field by name path
- `find_referencing_symbols` — find all usages of a symbol across the codebase
- `search_for_pattern` — regex search when symbol names are unknown

Prefer Serena's symbol tools over `Read`/`Grep` for source code exploration. Only fall back to file-based tools when Serena is unavailable or for non-code files (JSON configs, Markdown, etc.).

## Mandatory local checks before PR

Code style/lint in this repository is enforced via Ruff (`ruff check` + `ruff format`).

Quick loop (recommended for most PR iterations). `make lint` runs ruff, both mypy passes and the pre-commit hooks exactly as CI does. The pre-commit hooks include fixers (`trailing-whitespace`, `end-of-file-fixer`, `ruff-format`), so `make lint` may modify files in the working tree; review `git diff` afterwards. `pre-commit run --all-files` only sees files git tracks: `git add` new files before `make lint`, or the hooks (`check-json`, `check-toml`, ruff) skip them.

```bash
make lint
uv run pytest tests
```

The CI test jobs sync with `--no-group dev`, but your local `.venv` has the `dev` group: a test that imports a dev-only
package (PyYAML, for one) passes locally and fails in CI with `ModuleNotFoundError`. Import only runtime, extra or
`test`-group packages in `tests/`.

PyPy 3.11 on macOS arm64 segfaults on `copy` / `deepcopy` of `DefaultBotProperties`, and CI
does not reproduce it. PyPy also lacks some stdlib modules CPython has (`tracemalloc`), and the
PyPy CI jobs collect every test module, `benchmarks/` self-tests included. Before pushing a change
that copies or pickles models, or imports such a module, run the touched tests on a local PyPy,
in a separate environment so `.venv` is left alone:

```bash
UV_PROJECT_ENVIRONMENT=/tmp/aiogram-pypy uv sync --locked --all-extras --group test --python pypy3.11
UV_PROJECT_ENVIRONMENT=/tmp/aiogram-pypy uv run --no-sync python -m pytest <touched tests> -p no:cacheprovider
```

When touching `.github/**`, also run:

```bash
make lint-workflows
```

Without a GitHub token zizmor runs in offline mode and skips its online audits (known-vulnerable-actions and friends), which CI does run. To reproduce CI exactly, prefix `make lint-workflows` with `GH_TOKEN=$(gh auth token)`.

Full loop (run before final review request):

```bash
# Run quick loop first, then:
uv run pytest --redis redis://<host>:<port>/<db> tests  # when Redis storage paths are affected
uv run pytest --mongo mongodb://<user>:<password>@<host>:<port> tests  # when Mongo storage paths are affected
uv run --extra docs bash -c 'cd docs && make html'  # when docs or generated API docs are affected
```

If changes touch Redis/Mongo storage behavior, run integration variants too:

```bash
uv run pytest --redis redis://<host>:<port>/<db> tests
uv run pytest --mongo mongodb://<user>:<password>@<host>:<port> tests
```

Run these only if you have accessible Redis/Mongo instances in your environment.


## Changelog rules (CI-gated)

- Add `CHANGES/<issue-or-pr>.<category>.rst` unless PR has `skip news` label.
- Valid categories: `feature`, `bugfix`, `doc`, `removal`, `misc`.
- Changelog text must describe user-visible behavior changes, not process/org details.
- Do not edit `CHANGES.rst` directly for regular PRs.

## Bot API/codegen workflow (critical)

`aiogram` API layers are generated. For Bot API related work:

- Prefer editing generator inputs (`.butcher/**/*.yml`, aliases, templates) instead of hand-editing generated code.
- Do not manually edit `.butcher/**/entity.json` (parser/codegen will overwrite it).
- For new shortcuts, add alias/config in `.butcher` and regenerate.
- Regeneration flow:

```bash
uv run --extra cli butcher parse
uv run --extra cli butcher refresh
uv run --extra cli butcher apply all
```

- `butcher` is not shipped by the `cli` extra (`aiogram-cli` has no `butcher` script): it is the
  separate [aiogram/butcher](https://github.com/aiogram/butcher) repo. Install it into its own
  environment and run it from this repository root (`python -m butcher.shell.main apply all`).
  A fix that needs new generator behaviour lands in butcher first, then in `.butcher` config here.
- butcher formats with black, the repository with ruff, so raw `apply all` output differs from the
  committed files. Run `ruff check --fix aiogram/types aiogram/methods` (import order) and
  `ruff format aiogram` afterwards; on a clean tree that sequence yields an empty `git diff`, which
  is the check that a `.butcher` change survives regeneration.

For maintainers preparing an API/version bump only:

```bash
make update-api args=patch
```

`make update-api args=...` also runs version bump scripts and updates version-related files
(`aiogram/__meta__.py`, `README.rst`, `docs/index.rst`).

After regeneration, run lint/type/tests again.

## Maintainer review signals (recent PRs)

These patterns repeatedly appeared in maintainer feedback and should be treated as hard constraints:

- Keep generation path consistent: shortcuts/features should be added through `.butcher` config + generation, not ad-hoc manual edits.
- Keep test style consistent with existing suite; avoid introducing new dependencies for small tests.
- Preserve framework contracts (e.g., dispatcher/workflow data passed to startup/shutdown callbacks).
- When fixing generated API metadata/docs, update the source mapping in `.butcher` so future regenerations keep the fix.
- Pytest runs with `filterwarnings = ["error", ...]`: a new `warnings.warn(...)` in library code (e.g. a
  `DeprecationWarning`) fails every existing test that reaches it. Find those tests first, then either stop
  them from triggering it or assert it with `pytest.warns`.

## Benchmark corpus (`benchmarks/corpus/`)

- Pinned inputs for benchmarks and differential oracles; schema in `benchmarks/corpus/README.md`. `benchmarks/` is dev tooling, excluded from the sdist and wheel.
- Append-only: never edit a pinned file, add a new id. Every file needs a `MANIFEST.toml` entry with its sha256; `tests/test_corpus_manifest.py` enforces this and rejects anything matching a bot-token pattern. Corpus files are `-text` in `.gitattributes` so Windows checkouts keep the hashed bytes; keep new corpus paths under that rule rather than normalising line endings in the hash.
- `on_3x` records whether current 3.x decodes each update/response input. A change that makes 3.x accept or reject one (e.g. a forward-compat fallback) updates that field in the same PR.
- Real traces: record with `benchmarks/record/recorder.py` into the gitignored `benchmarks/record/raw/`, commit only the output of `benchmarks/record/redact.py`, after a manual review.
- Harness (A-05): `uv run python -m benchmarks run|compare|report`; the method, the CLI and how to read `compare` are
  in `benchmarks/README.md`. Cases are keyed by corpus ids and reach aiogram only through
  `benchmarks/adapters/aiogram3.py`. `compare` caches exported trees and venvs per sha in the gitignored `.benchmarks/`
  (delete it to rebuild), and `make bench` runs every case (about 10 minutes).

## Differential harness (`differential/`)

- `uv run python -m differential run --kind <smoke|model|request|routing> --left <side> --right <side> [--poison right]` compares two aiogram installs case by case; concepts, manifest schema and how to add an approved difference are in `differential/README.md`. Dev tooling: excluded from the sdist, never imported by `aiogram`.
- A new top-level dev directory is linted only if it is added to the Makefile `lint` paths and the pre-commit ruff `files` regex, and shipped unless it is in the hatch sdist `exclude`; `differential/` is in all three.
- Side scripts (`differential/sides/<adapter>/<kind>.py`) run under `python -I` in their own venv: stdlib + aiogram only, `differential/trace.py` loaded by path. Do not import other repository code from them.
- Side venvs live in the gitignored `.differential/`; `pypi:`/`git:` venvs are reused, so delete it to pick up a new release.
- A probe compared against `pypi:aiogram<4` must not record every optional field (`model_dump()` / `model_dump_json()`
  with their `None`s): after a Bot API bump the tree has fields the release lacks, and the weekly run fails until the
  next release. Record `exclude_unset` / `exclude_none` dumps, or strip the nulls. A new corpus input of kind `update`
  needs an access list in `differential/manifests/model.access.toml` (`tests/test_differential_model.py`).

## 4.0 planning tree (`v4/`)

- `v4/research/` and `v4/plans/` hold the aiogram 4.0 research and plans; `v4/plans/README.md` is the index and
  holds the `dev-3.x` → `dev-4.x` sync policy. `v4/` is excluded from the sdist (`pyproject.toml`).
- The repository is public: never add text to `v4/` that names or describes an unreleased security fix. Plans for
  such fixes stay out of the tree (listed as "(held back)" in the indexes) until the fix is released.
- The pre-commit `end-of-file-fixer` strips trailing blank lines from copied plan files; that is expected.
- The A-02 link-check script (in `v4/plans/A-contracts/A-02-apply-resolutions.md`, *Validation*) reports 9 known
  broken links in files no plan may edit: `v4/research/codex-review.md` (`../../../aiogram/...`) and
  `v4/plans/_TEMPLATE.md` (paths relative to a story folder). Any other hit is yours.
- A public plan's checklist may still point at work that belongs to a held-back plan. Skip such an item rather than
  paraphrasing it, and keep the *Notes* entry neutral ("left to the owner"); explain it only in the private report.
- `aiogram/_migration/registry.toml` is the migration registry (PD-13), plain data that is never imported. Its ids are
  append-only and sorted, and each kind stays in its PD-33 block: on `dev-3.x`, new hand-written entries go in
  AG4700–AG4799 and generated `api-ledger` entries in AG4800–AG4999. AG4001–AG4699 are allocated on `dev-4.x`
  only. The schema is documented in the file header, and `tests/test_migration_registry.py` enforces it.

## Developer design notes (`design/`)

- `design/testing-toolkit/` holds the architecture, invariants and decision log of `aiogram.test`. Read it before
  changing the toolkit, and update it in the same PR. Code cites decisions as "design decision TW-<n>".
- `design/` is excluded from the sdist and is not part of the Sphinx docs.

## Documentation work

For docs changes:

```bash
uv run --locked --extra docs sphinx-autobuild --watch aiogram/ --watch CHANGES.rst --watch README.rst docs/ docs/_build/
```

`sphinx-autobuild` is long-running by design.

Or quick build:

```bash
uv run --locked --extra docs bash -c 'cd docs && make html'
```

## PR quality checklist

Before requesting review:

1. Tests added/updated for behavior changes.
2. Local lint/type/tests pass.
3. Changelog fragment added (or `skip news` is justified).
4. If codegen-related: generated files and source config are both updated coherently.
5. PR body includes clear reproduction/validation steps.
