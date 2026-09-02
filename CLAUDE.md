# CLAUDE.md

Use @AGENTS.md as the source of truth for contribution workflow, checks, and Bot API codegen rules in this repository.

## rtk

Shell commands run under the `rtk` proxy (token-filtered output). Use these forms —
they are the ones verified against this project's toolchain:

| Task | Command |
|---|---|
| Tests | `rtk test uv run pytest tests -q` |
| Lint | `rtk ruff check --show-fixes --preview aiogram examples` |
| Format | `rtk ruff format aiogram tests scripts examples` |
| Types | `rtk mypy aiogram` |
| git / gh | `rtk git <sub>` / `rtk gh <sub>` |
| anything else | `rtk proxy <cmd>` (unfiltered but tracked) |

- **Never use `rtk pytest`.** It reports `No tests collected` on this suite even when
  tests fail — it masks failures. Always go through `rtk test uv run pytest …`, which
  keeps the project's `uv` environment and reports failures correctly. It is denied in
  `.claude/settings.json`.
- `rtk mypy` truncates the error text after `file:line: error:`. When you need the full
  message, rerun as `rtk proxy uv run mypy aiogram`.
- `rtk test`/`rtk err` accept a full command, so `uv run …` stays intact — which is what
  AGENTS.md mandates. `rtk ruff` / `rtk mypy` call the tool directly from the venv.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
