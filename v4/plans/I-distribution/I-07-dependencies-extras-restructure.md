# I-07 — Dependencies and extras restructure

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-05](I-05-pr-ci-structure-caching-coverage.md), [D-04](../D-client/D-04-drop-aiofiles-input-file-replayable.md), [F-07](../F-fsm/F-07-mongo-remove-motor-key-validation.md), [F-11](../F-fsm/F-11-callbackdata-without-pydantic.md), [C-13](../C-butcher/C-13-reexport-modules.md) |
| Blocks | [I-09](I-09-import-free-docs-build.md), [I-21](I-21-fresh-machine-install-rehearsal.md), [H-08](../H-testing-observability/H-08-otel-traces.md) |
| Gate-conditional | partly: the pydantic removal step needs F-11 / C-13, which follow D14 (gate-conditional, D104). The rest is gate-independent |
| Decisions | D14, D67, D68, D69, D70, D75, R25 |
| Sources | [08-build-release.md §8](../../research/08-build-release.md), [11-removals.md §4–5](../../research/11-removals.md), [17-cli.md](../../research/17-cli.md), [codex-review R25](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The 3.x `pyproject.toml` pins upper bounds everywhere:
- core: `aiohttp>=3.9.0,<3.15`, `pydantic>=2.7.0,<2.15`, `aiofiles<26.0`, `magic-filter<1.1`;
- extras: `redis[hiredis]<8`, `motor<3.8`, `pymongo<4.20`, `aiohttp-socks<1.12.0`;
- `requires-python = ">=3.11,<3.16"`.

It also ships a user-facing `docs` extra and a `cli` extra (`aiogram-cli`).

4.0 changes all of this:
- it drops pydantic (D14), aiofiles (D67) and motor (11 §5);
- `docs` becomes a dependency group and `cli` goes away (D68);
- the i18n extras split (D69);
- lower bounds only (D70), with CI on newest and lowest.

## Scope

**In:**
- Core dependencies = `aiohttp`, `magic-filter`, `certifi`, `typing-extensions` (while the floor is 3.11), lower bounds only.
- Remove `pydantic`, `aiofiles` and `motor` from `[project.dependencies]` / extras, and `motor-types` from the `dev` group.
- Extras exactly as 08 §8: `fast`, `redis`, `mongo` (pymongo only), `proxy`, `signature`, `i18n`, `fluent-runtime`,
  `fluent-compiler`, `otel`, `test`, `migrate`, `reload`. No `all` meta-extra.
  - Extras whose feature isn't merged yet are **not** added here: each feature plan adds its own extra with a lower
    bound (G-04 fluent, G-17 reload, H-08/H-09 otel, H-10 test, I-14 migrate).
  - This plan audits the final list.
- `docs` moves from `[project.optional-dependencies]` to `[dependency-groups]`. Drop the `cli` extra.
- Update `.readthedocs.yml` (today: `pip install .[docs,redis,mongo]`) to the docs group with `--no-install-project`
  (the R29 build itself is I-09).
- Update the Makefile `docs-*` targets (`uv run --extra docs …` → `--group docs`), the CI `--no-extra docs` flags, and
  AGENTS.md / CLAUDE.md commands on `dev-4.x`.
- CI:
  - keep and port the existing `lowest-deps` job (`uv sync --resolution lowest-direct`) on PRs;
  - add a **scheduled newest** job (`uv lock --upgrade` + full suite) that opens an issue on failure instead of
    blocking PRs (D70). It covers the magic-filter private integration and the optional pydantic interop hooks (R25).
- A guard test: no module under `aiogram/` imports `pydantic` or `aiofiles` at top level. Lazy imports inside the
  interop hooks are allowed.

**Out:**
- The code that replaces aiofiles (`FSInputFile`, downloads to `asyncio.to_thread`): D-04.
- Removing `MongoStorage`: F-07.
- `CallbackData` without pydantic: F-11.
- The pydantic interop hooks: B-06 / C-18.

## Checklist

- [ ] Rewrite `[project.dependencies]` and `[project.optional-dependencies]`, then regenerate `uv.lock`.
- [ ] **Decide how to drop the pins that violate D70** (proposed default):
      - remove every upper cap (`<3.15`, `<2.15`, `<8`, `<3.8`, `<4.20`, `<1.12.0`, `<1.1`, `<=5.0`) unless a
        known-breaking major exists. Each kept cap needs a comment with the issue URL;
      - drop the `requires-python` upper bound `<3.16`. On a not-yet-supported CPython, pip builds the sdist, which
        is preferable to silently resolving an old 3.x.
      Record each dropped and kept pin in Notes and flag them to the owner.
- [ ] `docs` → `[dependency-groups]`. Update `.readthedocs.yml`, Makefile, `tests.yml` and AGENTS.md / CLAUDE.md on `dev-4.x`.
- [ ] Remove the `cli` extra. `pip install "aiogram[cli]"` must keep resolving with a warning: pip ignores
      unknown extras with a warning, so verify this and record it.
- [ ] `tests/test_packaging/test_dependencies.py`:
      - core deps equal the expected set;
      - no extra named `docs`, `cli` or `all`;
      - every requirement has a lower bound;
      - no upper bound without a `# cap:` comment (parse `pyproject.toml` with `tomllib`).
- [ ] `tests/test_packaging/test_no_hard_imports.py`: walk `aiogram/` with `ast`. Fail on top-level
      `import pydantic` / `aiofiles` / `motor`.
- [ ] Scheduled `newest-deps` workflow, opening an issue on failure (`gh issue create`, deduplicated by title).
- [ ] Changelog fragment `CHANGES/<id>.removal.rst`: pydantic, aiofiles and motor are no longer dependencies, the
      `docs` / `cli` extras are gone, and new extras are listed.
- [ ] Migration-registry entries (PD-13, A-11 schema): `extra-cli-removed` and `extra-docs-removed`
      (removal-4.0, manual), plus `pydantic-not-installed` (manual: "add pydantic to your own deps if you used it
      transitively"), unless A-11 seeded them.

## Acceptance criteria

- `uv sync --locked`, `uv sync --resolution lowest-direct` and a `uv lock --upgrade` run all pass the full suite.
- `pip install aiogram` in a fresh venv installs no pydantic, aiofiles or motor (`pip list` check in the test job).
- Both packaging tests pass, and fail when a cap without a comment is added.
- The RTD config builds with the docs group (smoke; the full guarantee is I-09).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| `aiogram[pydantic]` extra | pydantic is neither required nor optional; hooks import lazily | D14, 11 §4 |
| `all` meta-extra | Not offered | 08 §8 |
| Keeping aiofiles | `to_thread` chunked IO is the same approach without a dependency | D67 |
| Keeping the `cli` extra pointing at aiogram-cli | Built-in CLI | D68, D75 |
| Blocking PRs on the newest-deps job | Opens an issue instead | D70 |

## Validation

```bash
uv lock && uv sync --locked --all-extras --group dev --group test
make dev
uv run pytest tests
uv sync --resolution lowest-direct && uv run pytest tests
uv run mypy aiogram
make lint && make lint-workflows
```

## Workflow notes

- Inputs: D-04 (aiofiles code gone), F-07 (motor gone), F-11 + C-13 (pydantic-free `CallbackData` and types).
- The pydantic step can land as a follow-up commit if F-11 lags. If B-13 is a no-go, only that step blocks.
- Outputs: the docs group (I-09) and the final extras list (I-03 matrix, I-10 Install page, I-21).

## Notes

(empty)
