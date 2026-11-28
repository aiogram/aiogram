# G-15 — Built-in CLI core (`aiogram`, `python -m aiogram`, plugins, `info`)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [B-01](../B-spike/B-01-crate-maturin-skeleton.md) |
| Blocks | [G-16](G-16-cli-run.md), [G-17](G-17-cli-reload.md), [G-18](G-18-cli-bot-commands.md), [G-19](G-19-cli-legacy-plugins.md), [G-21](G-21-aiogram-cli-final-release.md), [I-14](../I-distribution/I-14-migrate-engine.md), [I-21](../I-distribution/I-21-fresh-machine-install-rehearsal.md), [I-09](../I-distribution/I-09-import-free-docs-build.md) |
| Gate-conditional | no |
| Decisions | D75, D76, D77, D66, D68, R30 |
| Sources | [17-cli.md](../../research/17-cli.md), [19 R30](../../research/19-review-resolutions.md), [codex-review.md R30](../../research/codex-review.md), [08-build-release.md §8 (D68)](../../research/08-build-release.md), [16-support-policy.md §2](../../research/16-support-policy.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`aiogram-cli` 1.1.0 is a separate click-based proof of concept, pinned to `aiogram<4`. D75 replaces it with a CLI
inside the package, built on stdlib `argparse` and always installed, with no new dependencies. This plan builds the
skeleton every command plugs into:
- entry points;
- the plugin API;
- token handling;
- exit codes;
- `info`.

## Scope

**In:**
- `aiogram/cli/` package with `main(argv=None) -> int`.
- **Import-free parser spec:** the built-in commands' argparse definitions live in one module that imports only the
  stdlib (nothing from `aiogram`), so I-09 can load it by path and render the CLI reference statically; `main` builds
  the parser from it.
- A `[project.scripts] aiogram = "aiogram.cli:main"` entry in `pyproject.toml` (none exists today), and
  `aiogram/__main__.py` (none exists today), so that `python -m aiogram` and `aiogram` are the same CLI.
- **Plugin API**: `register(subparsers: argparse._SubParsersAction) -> None`. Each subcommand sets a handler via
  `set_defaults(func=…)`. Plugins come from the `aiogram.cli` entry-point group (`importlib.metadata.entry_points`).
  Built-in commands (`run`, `migrate`, `info`, `bot`) register through the same internal API.
- **Colours** only on a TTY, honouring `NO_COLOR`.
- **Exit codes**: `0` ok, `1` runtime error, `2` usage error (argparse default), `3` findings (`migrate check`).
- **Token handling** (shared helper for G-16/G-18):
  - `$BOT_TOKEN` or `--token-file PATH`;
  - `--token` is accepted with a warning that it ends up in shell history;
  - tokens are never echoed (D66), and errors are formatted through H-02's redaction where available.
- **`aiogram info`**: aiogram version, Rust core build (version, profile, target), Python version and
  implementation, free-threaded build and current GIL state (`sys._is_gil_enabled()` where present), wheel tag, and
  **installed optional packages** with their versions. The label says "installed optional packages", not "extras"
  (R30). `--json` is available. The output is ready to paste into bug reports.
- **`aiogram migrate`**: G-15 registers the `migrate` subcommand namespace (`fix` / `check`, with paths). The engine
  is I-14. The handler imports I-14's entry lazily and exits `2` with `pip install 'aiogram[migrate]'` when libcst is
  missing. If I-14 is not merged yet, the subcommand prints "not available in this build" and exits `2`.
- Remove the `cli` extra from `pyproject.toml` (D68). Coordinate with I-07.

**Out:**
- `run polling/webhook`: G-16. `--reload`: G-17. `bot …`: G-18. Legacy `aiogram_cli.plugins`: G-19.
- The migrate engine and rules: I-14..I-19.
- Scaffolding (`aiogram new`) and butcher commands: not in 4.0 (17 §2).

## Checklist

- [ ] `aiogram/cli/__init__.py` (`main`), `aiogram/__main__.py`, `[project.scripts]`.
- [ ] Internal registration API; built-ins registered through it.
- [ ] Entry-point loading for `aiogram.cli`: an import failure is reported on stderr (plugin name + exception) and
      does not break other commands.
- [ ] **Decide plugin name-collision precedence** (R30). Proposed default: built-in commands always win; between
      plugins, the first one loaded in sorted entry-point-name order wins; every collision prints a warning naming
      both distributions. Record in Notes and flag to owner.
- [ ] Token helper + redaction.
- [ ] `info` (text + `--json`), owned here. The core build metadata (version, profile, target) comes from B-01's
      `aiogram._core.build_info()`.
- [ ] Argparse definitions in an import-free module (stdlib only) that I-09 loads by path for the CLI reference.
- [ ] `migrate` namespace with lazy import + hint.
- [ ] Drop the `cli` extra. Migration-registry entry (PD-13) for the removed `aiogram[cli]` extra and the `aiogram-cli`
      package replacement (kind `removal-4.0`), unless I-07 already added it; check first.
- [ ] Docs: CLI reference page (18 Reference section), generated from the argparse parser where practical.
- [ ] Tests (100% coverage of new code): `main([...])` in-process, exit codes, `NO_COLOR`, a fake entry-point plugin
      via a monkeypatched `entry_points`, collision warning, broken plugin, `info --json` schema, `migrate` without
      libcst.
- [ ] Changelog fragment (`feature` + `removal` for the extra).

## Acceptance criteria

- `python -m aiogram --help` and `aiogram --help` print the same usage and exit `0`. `aiogram nosuch` exits `2`.
- `aiogram info --json` returns valid JSON with keys `aiogram`, `core`, `python`, `implementation`,
  `free_threaded`, `gil_enabled`, `wheel_tag`, `installed_optional_packages`.
- A plugin raising at import is reported, and `aiogram info` still works.
- `import aiogram` does **not** import `aiogram.cli` (no `argparse` cost at import).
- The parser-spec module loaded by file path in a bare interpreter (`python -I`, `importlib.util.spec_from_file_location`)
  builds the full parser without importing any `aiogram` module.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| click / typer | New dependency; stdlib argparse is enough | D75 |
| Keeping `aiogram-cli` as a separate package | Version skew, `aiogram<4` pin; replaced by core CLI | D68, D77 |
| Reporting "requested extras" in `info` | Installation metadata doesn't record them | R30 |
| Project scaffolding in 4.0 | Out of scope; can come as a plugin later | 17 §2 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
uv run aiogram info --json
```

## Workflow notes

- Inputs: B-01 (package skeleton and `_core` build metadata), I-07 (extras layout).
- Outputs: the plugin API and token helper for G-16, G-17, G-18 and G-19; the `migrate` namespace for I-14 (either
  can merge first); the import-free parser-spec module for I-09's static CLI reference; docs for I-10.

## Notes
