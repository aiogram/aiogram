# I-14 — `aiogram migrate` engine (check / fix)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-12](I-12-deprecation-machinery-registry-ci.md), [A-11](../A-contracts/A-11-migration-registry.md), [G-15](../G-features/G-15-cli-core.md) |
| Blocks | [I-15](I-15-receiver-inference.md), [I-16](I-16-codemod-imports-removals.md), [I-19](I-19-heuristic-behaviour-rules.md), [I-20](I-20-examples-port-smoke.md), [I-22](I-22-migration-rehearsal.md) |
| Gate-conditional | no |
| Decisions | D74, D76, D82, D100, PD-13, R28 |
| Sources | [16-support-policy.md §2.2–2.3](../../research/16-support-policy.md), [17-cli.md §1](../../research/17-cli.md), [18-docs-migration.md §2](../../research/18-docs-migration.md), [19 R28](../../research/19-review-resolutions.md), [codex-review R28](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

4.0 is a substantial migration (24 breaking changes, README). D74 promises two tools on the user's **3.x source**, both
shipping in 4.0:
- a codemod, `aiogram migrate fix`, dry-run by default;
- a checker, `aiogram migrate check`, with a non-zero exit on findings.

Users run them before upgrading, from an isolated environment:
`uvx --from 'aiogram[migrate]>=4' aiogram migrate check <path>` (R28).

R28 requires:
- findings classed **definite / heuristic / manual checklist**, each with a confidence level and a suppression;
- no rewrite that discards a result (e.g. `obj.replace(...)` not reassigned);
- conservative fallbacks for aliases and receivers.

Each finding's id is shared with the registry (PD-13) and the guide (D82).

This plan builds the engine with no rules. Rules come in I-16 to I-19.

## Scope

**In:**
- **Package and entry points.** `aiogram/migrate/` with `python -m aiogram.migrate {check,fix}` and the
  `aiogram migrate` subcommand registered through G-15's CLI core (argparse, D75).
- **Extra.** `aiogram[migrate]` = `libcst` (lower bound only, D70). Without libcst, exit 2 with an install hint.
- **Rule interface.** A rule has:
  - `id` (an `AG4xxx` id that must exist in `registry.toml`);
  - `finding_class` (definite / heuristic / manual), `confidence` (high / medium / low);
  - a libcst visitor producing `Finding(path, line, col, id, message, class, confidence)`;
  - an optional transformer producing a rewrite.
  - Rules are discovered from `aiogram/migrate/rules/`.
- **Engine behaviour:**
  - parses files with libcst and **never imports user code**;
  - takes a path list, honours `.gitignore`, `--exclude`, `--select` / `--ignore` ids;
  - `fix` applies only **definite** rewrites by default; `--heuristic` opts in to heuristic rewrites;
  - `--dry-run` is the default and prints a unified diff; `--write` applies.
- **Suppression.** `# aiogram-migrate: ignore[AG4012]` on the line, or file-level
  `# aiogram-migrate: ignore-file[AG4012]`.
- **Output.**
  - Text format: `path:line:col: AG4012 definite/high: message (guide URL)`.
  - `--format json` for CI.
  - Exit codes per 17 §1: `0` ok, `1` runtime error, `2` usage error, `3` findings.
- **Consistency check** (in `scripts/migration_registry.py check`, I-12): every rule id exists in the registry, and the
  registry's codemod-coverage field (✔ / partial / ✖) matches whether the rule has a transformer and its class. The
  guide and the tool then never disagree (D82).
- **Shared infrastructure for rules:** import resolution (`from aiogram.utils import markdown as md` aliases), a scope
  table for local names, and the inference hook that I-15 fills.

**Out:**
- All concrete rules (I-16 to I-19).
- Receiver inference (I-15).
- CLI core (G-15).

## Checklist

- [ ] `aiogram/migrate/{__init__,__main__,engine,finding,suppress,output,rules/__init__}.py`.
- [ ] **Decide whether `aiogram migrate` may import `_core`** (proposed default: yes. `uvx --from 'aiogram[migrate]>=4'`
      installs the Tier-1 wheel anyway, so the "import-free" guarantee of PD-13 covers **reading the registry**, not
      the CLI process. The engine must not *use* `_core`, which the test enforces with `_core` blocked except for
      `aiogram/__init__`. The alternative, making `aiogram/__init__` lazy via PEP 562, touches D16 and is out of scope).
      Record it in Notes and flag it to the owner.
- [ ] Register the `migrate` subcommand with G-15's plugin/subparser API (`register(subparsers)`). Until G-15 lands,
      `python -m aiogram.migrate` works on its own.
- [ ] Add the `migrate` extra to `pyproject.toml` (libcst lower bound).
- [ ] A dummy test rule under `tests/test_migrate/rules/` that exercises the definite fix, heuristic fix and manual
      paths, suppression, `--select` / `--ignore`, both output formats and the exit codes.
- [ ] Golden tests: input tree → expected diff (`tests/test_migrate/golden/<case>/{before,after}`). The harness is reused
      by I-16 to I-19.
- [ ] Docs: the Reference → CLI section for `migrate` (via the I-09 static CLI spec), and the Migration start-page
      opener ("run `aiogram migrate check`, then `aiogram migrate fix`", J-02 fills the rest).
- [ ] Tests (100% coverage of `aiogram/migrate/` engine code).
- [ ] Changelog fragment `CHANGES/<id>.feature.rst` (`aiogram migrate check/fix`). No registry entry of its own.

## Acceptance criteria

- `aiogram migrate check tests/test_migrate/golden/sample` exits 3 and prints the dummy findings. With all findings
  suppressed it exits 0, and with a bad flag it exits 2.
- `aiogram migrate fix` with no flags changes no file (mtime and content unchanged) and prints the diff. With `--write`,
  files equal the golden `after`.
- A rule whose id is missing from `registry.toml` fails `scripts/migration_registry.py check`.
- Running on a tree with a syntax error reports it as a runtime-error finding for that file and continues; that file
  exits 1 only if no other findings exist (documented precedence).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Importing user code / runtime introspection | Must run on 3.x source before upgrading, without the user's deps | D74, R28 |
| A checker that claims to find every incompatibility | Behaviour changes are manual-checklist items | R28, 18 §2 |
| Rewrites applied by default | Dry-run default; definite only unless `--heuristic` | D74, R28 |
| click-based CLI | stdlib argparse | D75 |

## Validation

```bash
make dev
uv sync --extra migrate
uv run pytest tests/test_migrate -q
uv run pytest tests
uv run mypy aiogram
uv run python scripts/migration_registry.py check
make lint
```

## Workflow notes

- Inputs: I-12 (registry loader), A-11 (ids), G-15 (CLI core; soft, needed only for the subcommand step).
- Outputs:
  - rule API and golden harness, used by I-15 to I-19;
  - JSON output, used by I-22 to measure coverage.
- I-16, I-18 and I-19 can run in parallel once this and I-15 land.

## Notes

(empty)
