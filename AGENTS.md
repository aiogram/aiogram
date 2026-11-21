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

Quick loop (recommended for most PR iterations). `make lint` runs ruff, both mypy passes and the pre-commit hooks exactly as CI does. The pre-commit hooks include fixers (`trailing-whitespace`, `end-of-file-fixer`, `ruff-format`), so `make lint` may modify files in the working tree; review `git diff` afterwards.

```bash
make lint
uv run pytest tests
```

When touching `.github/**`, also run:

```bash
make lint-workflows
```

Without a GitHub token zizmor runs in offline mode and skips its online audits (known-vulnerable-actions and friends), which CI does run. To reproduce CI exactly, prefix `make lint-workflows` with `GH_TOKEN=$(gh auth token)`.

To run a test file on another interpreter of the CI matrix (3.11–3.15, 3.14t) without touching `.venv`:

```bash
UV_PROJECT_ENVIRONMENT=/tmp/venv-3.11 uv run -p 3.11 --all-extras --group test pytest tests/<path>
```

On Python 3.14+ `typing.get_type_hints` inside
`__init_subclass__` raises `NameError` for an unquoted reference to the class itself unless it is called with
`format=annotationlib.Format.FORWARDREF`.

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


## Testing

Suite strategy (4.0, D88):

- `tests.mocked_bot.MockedBot` for unit tests of one component: queue replies with `bot.add_result_for(...)`, inspect
  `bot.get_request()` / `bot.session.requests`.
- The `aiogram.test` toolkit for new end-to-end scenarios (dispatcher + FSM + scenes + filters + errors).
- No mass rewrite of existing tests onto the toolkit.
- The 100% coverage rule is unchanged.

`MockedSession` builds the JSON wire envelope and runs it through `BaseSession.check_response`, so unit tests keep
exercising the real error mapping (`TelegramBadRequest`, `TelegramRetryAfter`, ...). Its only model-layer dependency is
the `_wire_default` helper. `tests/mocked_bot.py` must not mention `pydantic` at all, not even in a comment: a guard
test (`tests/test_mocked_bot.py`) greps the source.

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

## 4.0 planning tree (`v4/`)

- `v4/research/` and `v4/plans/` hold the aiogram 4.0 research and plans; `v4/plans/README.md` is the index and
  holds the `dev-3.x` → `dev-4.x` sync policy. `v4/` is excluded from the sdist (`pyproject.toml`).
- The repository is public: never add text to `v4/` that names or describes an unreleased security fix. Plans for
  such fixes stay out of the tree (listed as "(held back)" in the indexes) until the fix is released.
- The pre-commit `end-of-file-fixer` strips trailing blank lines from copied plan files; that is expected.
- A plan that defines an API other plans consume (F-08's converter core for F-09 / F-11 / F-12) starts with a design
  the owner approves (API sketch, layout, open questions) before any code: F-08's first implementation was redone.

## Native extension (`dev-4.x`)

- The build backend is maturin: `crates/aiogram-core` builds `aiogram._core`, so `uv sync` needs `rustup`
  (`rust-toolchain.toml` pins the toolchain). `uv run` rebuilds it (release profile) when a `*.rs` or `Cargo.toml`
  under `crates/aiogram-core`, the workspace `Cargo.toml`, `Cargo.lock` or `.cargo/config.toml` changes; `make dev`
  installs a fast debug build, `make bench` a release one. Nothing on the 3.x import path loads `_core`
  (`tests/test_core/test_build.py` checks it).
- Rust checks: `cargo fmt --all --check`, `cargo clippy --workspace --all-targets -- -D warnings` (`unwrap`,
  `expect`, `panic!`, `todo!`, `unimplemented!` are denied), `cargo test --workspace`. CI: `.github/workflows/core.yml`.
- `clippy.toml`'s `allow-*-in-tests` covers `#[test]` functions and `#[cfg(test)]` modules only. Helpers in an
  integration test crate (`crates/*/tests/*.rs`) need `#![allow(clippy::unwrap_used)]` at the top of the file.
- The version lives in `aiogram/__meta__.py` and is copied, static, into `pyproject.toml` and
  `crates/aiogram-core/Cargo.toml`. Only change it with `make bump`: it writes both copies and refreshes
  `Cargo.lock` and `uv.lock` (`uv sync --locked` fails otherwise). `test_build.py` asserts they match.
- `tests/typing/` holds mypy-only `assert_type` files, never collected by pytest; run them with `make typing`.
- The stubs are hand-written (PD-36): `aiogram/_core/__init__.pyi` for the root (`__version__`, `build_info`) and
  one `aiogram/_core/<name>.pyi` per native submodule. The directory holds stubs only (no `.py`); the `.so` beside
  it wins at import. After changing the `_core` surface, update the stubs and run `make stubtest` (also part of
  `make lint`); stubtest needs the built extension and walks every submodule stub on its own.
- A new native group = one Rust `mod` with `pub fn register(&Bound<PyModule>)` + one
  `register_submodule(m, "<name>", <name>::register)` line in `lib.rs` + one `aiogram/_core/<name>.pyi` (with
  `__all__`, and `from . import <name> as <name>` in `__init__.pyi`). Its classes get
  `#[pyclass(module = "aiogram._core.<name>")]`. Nothing else: `test_build.py` derives the submodule list from the
  stub files and imports each in a fresh process. Consumers import names directly
  (`from aiogram._core.<name> import X`); the root holds no flat aliases.
- Converter core (PD-36, F-08 plan-10): `aiogram/utils/converters.py` is the public, stdlib-only declaration API
  (`field`, `Key`, `Discriminator`, `Converter`, ready-made converters, `ConversionError`); `aiogram/utils/_converters.py`
  resolves annotations and holds `ModelBase`; `crates/aiogram-core/src/conv/` does every conversion. `import aiogram`
  must not import `_converters` (it loads `_core`); `tests/test_core/test_build.py` checks it.
  - The Python -> Rust interface is the typed constructors in `conv/ir.rs` (`Kind`, `Field`, `KindCell`) and
    `ModelCore`, declared in `aiogram/_core/conv.pyi`. Rust never reads resolver attributes by name. A new kind needs a
    constructor (and its stub), a `Data` variant, and its arm in `json/load.rs`, `json/parse.rs`, `json/dump.rs`,
    `json/write.rs`, `check.rs` and `flat/` (or a "no flat form" there).
  - Errors stay Rust `Line`s until `errors::materialize` builds one `ConversionError`; message text and locs are
    checked by the contract suite (`tests/test_utils/test_converters.py`), so change both together.
  - `conv/native/` is pure Rust, tested against CPython-generated vectors; keep it free of the Python API.
  - Rebuild before testing a crate change (`make dev`, then `uv run --no-sync pytest`): a stale `_core.*.so` makes
    tests fail, crash or pass for the wrong reason.
  - A build outside the worktree (a scratch copy, an older commit from `git archive`) goes through
    `maturin build -i <python>` and the wheel's `_core*.so`: a plain `cargo build` cdylib segfaults at import.

## Butcher (`dev-4.x`)

- The 4.x generator is the pure-Rust `crates/butcher` (no pyo3), run as `cargo xtask butcher <cmd>`; the Python
  `.butcher/` flow above is 3.x only. `butcher/` holds its committed data: `snapshots/<api_version>/` (current API
  version only, git history is the archive), `overlay/`, `ledger.toml`.
- The IR (`crates/butcher/src/ir.rs`) is the contract of every C plan. It only grows by optional fields (`Option` /
  `Vec`, omitted when empty), so older snapshots still load; a rename or removal regenerates the committed
  snapshots in the same PR. Files under `butcher/` are compared byte for byte (`.gitattributes` keeps them LF).

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
