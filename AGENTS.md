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

Run `ruff check --fix` only on the files you touched: on `tests` or `aiogram` it also rewrites unrelated
files (it did to `tests/test_api/test_client/test_session/test_aiohttp_session.py`); check `git status` after it.

Quick loop (recommended for most PR iterations). `make lint` runs ruff, both mypy passes and the pre-commit hooks exactly as CI does. The pre-commit hooks include fixers (`trailing-whitespace`, `end-of-file-fixer`, `ruff-format`), so `make lint` may modify files in the working tree; review `git diff` afterwards. `pre-commit run --all-files` only sees files git tracks: `git add` new files before `make lint`, or the hooks (`check-json`, `check-toml`, ruff) skip them.

```bash
make lint
uv run pytest tests
```

The CI test jobs sync with `--no-group dev`, but your local `.venv` has the `dev` group: a test that imports a dev-only
package (PyYAML, for one) passes locally and fails in CI with `ModuleNotFoundError`. Import only runtime, extra or
`test`-group packages in `tests/`.

When touching `.github/**`, also run:

```bash
make lint-workflows
```

Without a GitHub token zizmor runs in offline mode and skips its online audits (known-vulnerable-actions and friends), which CI does run. To reproduce CI exactly, prefix `make lint-workflows` with `GH_TOKEN=$(gh auth token)`.
actionlint runs shellcheck on `run:` scripts only when `shellcheck` is on `PATH` (CI runners have it) and
skips it silently otherwise: install it (`brew install shellcheck`) or a SC#### error shows up only in CI.

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
- Token safety: assert with `tests/token_safety.py` (`FAKE_TOKEN`, `assert_token_absent`). `raise ... from None`
  inside `except` still sets `__context__` (only suppressed), so the helper walks the chain a traceback prints, not
  `__context__` / `.original`, which hold the raw aiohttp error by design.
- `aresponses` intercepts every host, `127.0.0.1` included: a test that needs a real unreachable hop (a redirect to
  a closed port) uses `aiohttp.test_utils.TestServer` without the `aresponses` fixture.
- `aiogram.test` deep-copies worlds, including their FSM storage (`tests/test_testing/test_world.py`). A
  `threading.Lock` cannot be copied, so a storage or isolation class that holds one needs `__getstate__` /
  `__setstate__` (the copy gets its own lock) and a `__copy__` that shares it (`MemoryStorage`, F-01).
- `tests/test_fsm/storage/test_storages.py::TestStorages` also runs on `MinimalStorage` (`tests/conftest.py`), a
  storage with only the abstract `BaseStorage` methods: a new non-abstract `BaseStorage` method needs a fallback that
  passes there, and a new shared case must not rely on a built-in storage's extras.

`MockedSession` builds the JSON wire envelope and runs it through `BaseSession.check_response`, so unit tests keep
exercising the real error mapping (`TelegramBadRequest`, `TelegramRetryAfter`, ...). Its model-layer dependencies are
the `_wire_default` helper and `bot_full_info` (`model_fields`). `tests/mocked_bot.py` must not mention `pydantic`
at all, not even in a comment: a guard test (`tests/test_mocked_bot.py`) greps the source.

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
uv run butcher parse
uv run butcher refresh
uv run butcher apply all
```

- `butcher` is not a dependency of this project (`uv run butcher` only works once it is installed): it is the
  separate [aiogram/butcher](https://github.com/aiogram/butcher) repo. Install it into its own
  environment and run it from this repository root (`python -m butcher.shell.main apply all`).
  A fix that needs new generator behaviour lands in butcher first, then in `.butcher` config here.
  The build commands are in `.claude/skills/bot-api-bump/SKILL.md`, step 1.
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
- The bench builds every `routing/*.toml` topology, and its adapter knows only `command`, `text_eq` and `pass`. A
  topology using any other kind (all the A-10 oracle scenarios) carries `bench = false`;
  `tests/test_differential_routing.py` enforces both sides. The PR CI does not run the bench, so a missed key only
  shows in the weekly Benchmarks run.

## Differential harness (`differential/`)

- `uv run python -m differential run --kind <smoke|model|request|routing> --left <side> --right <side> [--poison right]` compares two aiogram installs case by case; concepts, manifest schema and how to add an approved difference are in `differential/README.md`. Dev tooling: excluded from the sdist, never imported by `aiogram`.
- A new top-level dev directory is linted only if it is added to the Makefile `lint` paths and the pre-commit ruff `files` regex, and shipped unless it is in the hatch sdist `exclude`; `differential/` is in all three.
- Side scripts (`differential/sides/<adapter>/<kind>.py`) run under `python -I` in their own venv: stdlib + aiogram (and its runtime dependencies, such as pydantic) only, `differential/trace.py` (and `wire.py`, its sibling) loaded by path. Do not import other repository code from them.
- Side venvs live in the gitignored `.differential/`; `pypi:`/`git:` venvs are reused, so delete it to pick up a new release.
- A manifest entry without `when` is active in 3.x-vs-3.x runs too; list it in `THREE_X_ENTRIES` of `tests/test_differential_framework.py`, which otherwise requires `when = "aiogram4"`.
- A probe compared against `pypi:aiogram<4` must not record every optional field (`model_dump()` / `model_dump_json()`
  with their `None`s): after a Bot API bump the tree has fields the release lacks, and the weekly run fails until the
  next release. Record `exclude_unset` / `exclude_none` dumps, or strip the nulls. A new corpus input of kind `update`
  needs an access list in `differential/manifests/model.access.toml` (`tests/test_differential_model.py`).
- A comparator decides on what the left side (the 3.x reference) records in `meta`, never on "what the right side
  did". The routing side puts its reference facts there (surviving candidates, raise paths, same-case
  registrations), and that is how its comparators stay narrow. A record matches one manifest entry, so a difference
  that holds everywhere (D12, D34, D111) is applied inside every comparator of the kind, not by a second entry.
- A concurrent routing case (`group`) must not depend on thread timing: a sync filter hops to `asyncio.to_thread`,
  so use `command` (async) filters there.
- A dev-4.x tree still reports a 3.x `__version__`, so both sides get the `aiogram3` adapter and the
  `when = "aiogram4"` entries stay inert. The routing kind therefore runs only for dev-3.x (E-01 already
  removed the D12 keys), and `tests/test_differential_routing.py` skips the checks that need a 3.x record there.

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
  installs a fast debug build, `make bench` a release one (then runs the benchmark cases). Nothing on the 3.x
  import path loads `_core` (`tests/test_core/test_build.py` checks it).
- Rust checks: `cargo fmt --all --check`, `cargo clippy --workspace --all-targets -- -D warnings` (`unwrap`,
  `expect`, `panic!`, `todo!`, `unimplemented!` are denied), `cargo test --workspace`. `make lint` runs fmt and
  clippy too (`lint-rust`; CI runs `lint-python` in Lint and `lint-rust` in Rust).
- CI (`.github/workflows/tests.yml`, structure in its header): `build-wheels` builds one release wheel per leg, cached
  on the hash of the extension's inputs, and the other jobs copy only `aiogram/_core.*` out of it into the checkout
  (`scripts/ci_use_wheel.py`), never `pip install` it: the cached wheel's Python files are stale on a Python-only
  PR. A new input of the extension goes into that cache key and into `[tool.uv] cache-keys` together; a new
  Rust-side path into the `RUST` pattern of the `plan` job. PRs run a reduced leg set, push to `dev-4.x` the full
  matrix; a `schedule` trigger does not fire on `dev-4.x` (not the default branch).
- Rust coverage locally: `source <(cargo llvm-cov show-env --sh)`, `cargo test --workspace`, `make dev`, `uv run
  pytest`, `cargo llvm-cov report` (what the CI Rust job runs). The instrumentation goes through a rustc wrapper
  that cargo's fingerprint does not see, so a later plain `make dev` keeps the instrumented build (it writes
  `default_*.profraw` files): `cargo clean -p aiogram-core -p butcher -p xtask` afterwards.
- `clippy.toml`'s `allow-*-in-tests` covers `#[test]` functions and `#[cfg(test)]` modules only. Helpers in an
  integration test crate (`crates/*/tests/*.rs`) need `#![allow(clippy::unwrap_used)]` at the top of the file.
- The version lives in `aiogram/__meta__.py` and is copied, static, into `pyproject.toml` and
  `crates/aiogram-core/Cargo.toml`. Only change it with `make bump`: it writes both copies and refreshes
  `Cargo.lock` and `uv.lock` (`uv sync --locked` fails otherwise). `test_build.py` asserts they match.
  Pre-releases are `X.Y.ZaN` / `bN` / `rcN`: the crate gets the semver form (`4.0.0-alpha.1`, which `build.rs`
  turns back for `_core.__version__`) and pyproject the matching `Development Status` classifier.
- `import aiogram` first runs `aiogram/_native.py`: a `find_spec` lookup (no load) that raises an `ImportError`
  naming the interpreter tag when no `_core` extension fits. A stub-only `aiogram/_core/` resolves as a
  namespace package, so without a built `.so` (`make dev`) nothing imports.
- `tests/test_packaging/` checks built artifacts and is skipped unless `AIOGRAM_DIST_DIR` points at a directory
  with one wheel and one sdist (`maturin build --release -o <dir>`, `maturin sdist -o <dir>`); CI: `packaging`
  in `tests.yml`. The sdist's top-level set is exact: a new top-level file maturin packs fails it. The sdist
  ships no `rust-toolchain.toml` (rustup would force that toolchain on every source build); its `Cargo.lock`
  still lists the dev crates, so cargo commands on an unpacked sdist cannot use `--locked`.
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
- Decode core of the Telegram types (B-03): `crates/aiogram-core/src/decode/`, pure Rust with no Python surface.
  `decode/tests/types.rs` holds hand-written types in the shape B-04 writes and C-18 emits. The corpus tests read
  `benchmarks/corpus/wire/<id>.json` from disk. jiter checks `\u` escapes even in skipped values (`known_skip`), so a
  lone surrogate anywhere in the input is a decode error, not only in decoded strings.
- B-14 on top of it:
  - unions (`decode/union.rs`), the depth guard in `Decode::decode` (128 objects, stacker re-entry), the
    `Unknown…` hook (`Cursor::report`, `decode/seen.rs`) and the envelope / `getUpdates` entry points
    (`decode/envelope.rs`);
  - jiter's `known_skip` also stops at 200 nested levels relative to where it starts. A failure path that must find
    a value's end after jiter failed (a batch element, an absorbed union member) uses `decode/scan.rs`, which checks
    only strings and bracket balance;
  - a `\uXXXX` escape typed into an agent's tool call can arrive decoded in the written file: build such test
    input at runtime (`format!("{}u0075", '\\')`) and grep the file afterwards.
- The A-02 link-check script (in `v4/plans/A-contracts/A-02-apply-resolutions.md`, *Validation*) reports 9 known
  broken links in files no plan may edit: `v4/research/codex-review.md` (`../../../aiogram/...`) and
  `v4/plans/_TEMPLATE.md` (paths relative to a story folder). Any other hit is yours.
- A public plan's checklist may still point at work that belongs to a held-back plan. Skip such an item rather than
  paraphrasing it, and keep the *Notes* entry neutral ("left to the owner"); explain it only in the private report.
- `aiogram/_migration/registry.toml` is the migration registry (PD-13), plain data that is never imported. Its ids are
  append-only and sorted, and each kind stays in its PD-33 block: on `dev-3.x`, new hand-written entries go in
  AG4700–AG4799 and generated `api-ledger` entries in AG4800–AG4999. AG4001–AG4699 are allocated on `dev-4.x`
  only. The schema is documented in the file header, and `tests/test_migration_registry.py` enforces it.

## Butcher (`dev-4.x`)

- The 4.x generator is the pure-Rust `crates/butcher` (no pyo3), run as `cargo xtask butcher <cmd>`; the Python
  `.butcher/` flow above is 3.x only. `butcher/` holds its committed data: `snapshots/<api_version>/` (current API
  version only, git history is the archive), `overlay/`, `ledger.toml`.
- The IR (`crates/butcher/src/ir.rs`) is the contract of every C plan. It only grows by optional fields (`Option` /
  `Vec`, omitted when empty), so older snapshots still load; a rename or removal regenerates the committed
  snapshots in the same PR. Files under `butcher/` are compared byte for byte (`.gitattributes` keeps them LF).
- `sources/errors.rs` (C-05) turns `errors.json` into `ir.errors.json`. Its templates overlap (`entity %s` matches the longer
  entity messages), so a lookup is the exact message first, then the matching template with the longest literal
  (`literal_len`). The live check is `BUTCHER_LIVE=1 cargo test -p butcher errors_counts -- --ignored`; it pins the
  message and template counts of the current file, so a routine Telegram addition fails it until the numbers are updated.
- `overlay/` (C-06): `Overlay::load` enforces the schema (`deny_unknown_fields`, no stray files), `Overlay::check` the
  references into the IR. Completeness rules (every method has `idempotent`, ...) are `butcher check`'s (C-23), not the
  loader's. Avoid `#[serde(untagged)]` in schemas loaded through `serde_path_to_error`: it replaces the inner
  "unknown field" error with "did not match any variant" (the fill value has a hand-written `Deserialize` instead).
- Fill-DSL (C-07, `src/dsl.rs`): `dsl::apply` resolves shortcut fills, guards and `events.toml` into `Ir.shortcuts` /
  `Ir.events`; grammar and rules in `butcher/overlay/README.md`. Paths use Python names (`names.toml`), steps store
  wire names. `tests/fixtures/dsl/` is the 3.x corpus (all 189 `aliases.yml` shortcuts); 3.x shared `ignore` anchors
  list params some target methods lack, which C-06's check rejects, so a translator drops them.
- `cargo test -p butcher <name>` filters by test name, not by file: `cargo test -p butcher overlay` skips most of
  `tests/overlay.rs`. Run a test file with `--test <file>`.
- A new workspace crate stays out of the sdist and the wheel: maturin rewrites the sdist's `members` to
  `crates/aiogram-core` and its path dependencies. Check with `uv build` (sdist, then a wheel built from it).

## CLI (`aiogram/cli/`, `dev-4.x`)

- `aiogram/cli/_spec.py` imports only the stdlib: the docs build loads it by path. A new built-in command goes
  there as a `register_<name>(subparsers)` in `BUILTINS`, with `set_defaults(func="module:attr")` (the handler module
  is imported only when the command runs) and `add_token_arguments` for a token. `tests/test_cli` builds the
  parser under `python -I` with no `aiogram` module loaded.
- `import aiogram` already loads `argparse` (`unittest.mock.sentinel` in `aiogram/dispatcher/event/bases.py`), so an
  import-cost test checks for `aiogram.cli` modules, not `argparse`.
- CI tests the checkout with `--no-install-project`: no `aiogram` console script and no `aiogram` dist-info. Tests
  check the `[project.scripts]` declaration and run `main` as the wrapper does, never the installed script;
  `runpy` on `aiogram.__main__` fails under pytest's import hook there, so use a `python -m aiogram` subprocess.

## Logging (`dev-4.x`)

- Framework loggers come only from `aiogram/loggers.py` (`loggers.<name>` or `loggers.get_logger("aiogram.x")`); the
  factory installs the record filters on each logger, because Python never runs an ancestor logger's filters for a
  child's records. `tests/test_loggers.py` fails on any `getLogger(` call elsewhere in `aiogram/`.
- `pytest --cov=aiogram.loggers` (a dotted single module) imports that module more than once; the factory replaces
  marked stale filters (`aiogram_framework_filter`), so a new framework filter needs the same marker.
- A test `logging.Handler` subclass must not set `self.lock`: `Handler.handle()` holds it around `emit()`, and a
  plain `threading.Lock` there deadlocks the test.
- Token masking has one pattern: `loggers._TOKEN_PATTERN` (H-02), also used by the CLI's `redact()`. It has no `\b`,
  because in `/bot123456:...` no word boundary comes before the id. It keeps `(?<!\d)`: without it, `\d{5,}` retries
  at every digit, and a long digit run with no colon takes quadratic time.
- A test that walks `logging.Logger.manager.loggerDict` runs in a subprocess. The pytest process holds `aiogram.*`
  loggers that other tests created with a plain `logging.getLogger`.

## Async generators and file IO

- File IO goes through `aiogram/utils/_fileio.py` (`iter_file`, `write_stream`): `asyncio.to_thread` with the open and
  the close shielded, so a cancellation never leaks a descriptor. Tests count open handles by wrapping `builtins.open`
  (`tests/test_utils/test_fileio.py`).
- A method that only forwards another async generator returns it (`def read(...)`) instead of re-yielding it:
  `shutdown_asyncgens()` finalizes a wrapper and the inner generator concurrently and raises
  `aclose(): asynchronous generator is already running`.
- `ruff check --fix` / `ruff format` over all of `tests/` rewrites unrelated files on this branch: pass the paths you touched.
- Downloads go through `BaseSession._download_stream()`, never `stream_content()` directly: it hands a
  `DownloadTimeout` only to overrides whose `timeout` default is one (or that forward `**kwargs`), and gives a 3.x
  `timeout: int` override the total plus one warning per class. A session in this repo or a test that overrides
  `stream_content` declares `timeout: DownloadTimeout | float = DEFAULT_DOWNLOAD_TIMEOUT`, or the warning fails the
  suite under `filterwarnings = error`.

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
