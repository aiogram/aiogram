# G-17 — `--reload` via watchfiles

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [G-16](G-16-cli-run.md), [G-15](G-15-cli-core.md) |
| Blocks | — |
| Gate-conditional | no |
| Decisions | D78, D70 |
| Sources | [17-cli.md D78, §1](../../research/17-cli.md), [08-build-release.md §8](../../research/08-build-release.md), [codex-review.md R30](../../research/codex-review.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Development reload was the main feature of `aiogram-cli`'s `develop` command. D78 keeps it in the built-in CLI
behind the `aiogram[reload]` extra (watchfiles).

## Scope

**In:**
- `--reload` on `run polling` and `run webhook`. watchfiles' `run_process` restarts a **child process** on `*.py`
  changes, plus `--reload-include` globs (e.g. `locales/**`, so G-03/G-04 catalogs reload too).
- The child runs the normal Runner, so `dp.shutdown` fires on every restart (SIGINT/SIGTERM to the child, with a
  grace period).
- `--reload` without the extra exits `2` with `pip install 'aiogram[reload]'`.
- Extra `reload = ["watchfiles>=…"]`, lower bound only (D70). Coordinate with I-07.

**Out:**
- In-process hot reload (module reimport): rejected below.

## Checklist

- [ ] `--reload`, `--reload-include` (repeatable), `--reload-dir` (default: cwd).
- [ ] Child-process supervision. The parent never imports the user app (so a syntax error in the app doesn't kill
      the reloader).
- [ ] Extra `reload` in `pyproject.toml`.
- [ ] **Decide `run webhook --reload` with `--set-webhook`** (proposed default: `setWebhook` runs only in the first
      child, so restarts do not re-call it; or reload + set-webhook is rejected with a usage error; pick one) —
      record in Notes and flag to owner.
- [ ] Docs: development section of the deploying page.
- [ ] Tests (100% coverage of new code): the missing-extra hint; a subprocess test that touches a file and observes a
      restart with shutdown hooks run (skipped when watchfiles is absent; CI installs it).
- [ ] Changelog fragment (`feature`).

## Acceptance criteria

- Editing a watched `.py` file restarts the child within 2 s. The old child's `dp.shutdown` ran (marker file).
- Editing `locales/uk/LC_MESSAGES/messages.po` with `--reload-include 'locales/**'` triggers a restart.
- Without watchfiles: `aiogram run polling app:dp --reload` exits `2` and prints the install hint.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| In-process module reimport | Stale objects, routers registered twice | 17 §1 (child process) |
| watchfiles as a core dependency | Dev-only feature; extra | D78 |

## Validation

```bash
make dev
uv sync --extra reload
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: G-16 (`run` commands). Output: none consumed by other plans. I-21 checks the extra in the fresh-machine
  install.

## Notes
