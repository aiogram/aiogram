# G-19 — Legacy `aiogram_cli.plugins` loading and click adapter

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [G-15](G-15-cli-core.md), [A-11](../A-contracts/A-11-migration-registry.md), [I-12](../I-distribution/I-12-deprecation-machinery-registry-ci.md) |
| Blocks | [G-21](G-21-aiogram-cli-final-release.md) |
| Gate-conditional | no |
| Decisions | D77, D71, D72, R30, PD-13 |
| Sources | [17-cli.md D77](../../research/17-cli.md), [19 R30](../../research/19-review-resolutions.md), [codex-review.md R30](../../research/codex-review.md), [16-support-policy.md §1](../../research/16-support-policy.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Third-party `aiogram-cli` plugins register click commands in the `aiogram_cli.plugins` entry-point group. D77 keeps
them visible under the new `aiogram` command for one deprecation window, so their users aren't stranded on upgrade.

## Scope

**In:**
- Load the `aiogram_cli.plugins` group alongside `aiogram.cli`. Each loaded legacy plugin emits one
  `AiogramDeprecationWarning` per process, naming the plugin and pointing to the `register(subparsers)` API.
- **Click adapter**: a legacy click command becomes an argparse subcommand that forwards the remaining argv verbatim
  to the click command (`standalone_mode=False`). `aiogram <cmd> --help` shows click's help. Exit codes map to G-15's
  codes (click `UsageError` → `2`).
- **click is imported only when installed and a legacy entry point exists.** Without click, legacy plugins are
  reported as "requires click" and skipped (R30).
- Incompatible plugins are reported, not fatal. These are plugins whose import fails, or whose distribution pins
  `aiogram<4` / depends on `aiogram-cli` (detected via `importlib.metadata` requirements). The report goes to stderr,
  and `aiogram info` lists them too.
- A migration-registry entry (PD-13): kind `deprecation-4.x`, removal no earlier than the D71 window.

**Out:**
- The `aiogram-cli` final release: G-21.
- Rewriting third-party plugins.

## Checklist

- [ ] Legacy group loader + deprecation warning (via the I-12 machinery and registry id).
- [ ] Click adapter with argv forwarding, help and exit-code mapping.
- [ ] Lazy click import; "requires click" report.
- [ ] Incompatible-plugin detection and report, also shown in `aiogram info`.
- [ ] Name collisions follow G-15's precedence decision. A legacy plugin never shadows a built-in.
- [ ] Registry entry + changelog fragment (`removal`/deprecation).
- [ ] Docs: plugin authoring page, with the old → new API side by side.
- [ ] Tests (100% coverage of new code): fake legacy entry point with a click command; click absent; broken plugin;
      collision with a built-in.

## Acceptance criteria

- A fake legacy plugin `hello` registered under `aiogram_cli.plugins` runs as `aiogram hello --name x`, prints
  click's output, and the deprecation warning is emitted once.
- With click uninstalled, `aiogram --help` works and lists the plugin as skipped ("requires click").
- A legacy plugin named `run` does not replace the built-in `run`; a warning names it.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Dropping legacy plugins outright | Users stranded; one D71 window promised | D77 |
| Depending on click | Core CLI has no new dependencies | D75 |
| Repairing incompatible plugin metadata at runtime | Impossible; report instead | R30 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: G-15 (loader, precedence), A-11 / I-12 (registry + deprecation machinery).
- Output: G-21 documents the upgrade path that relies on this adapter.

## Notes
