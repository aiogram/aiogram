# C-01 — butcher crate, xtask entry point, IR model, snapshot format

| Field | Value |
|---|---|
| Status | `done` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [B-01](../B-spike/B-01-crate-maturin-skeleton.md), [A-01](../A-contracts/A-01-bootstrap-dev-4x.md) |
| Blocks | [C-02](C-02-fetch-provenance.md), [C-03](C-03-html-adapter.md), [C-04](C-04-openapi-adapter.md), [C-05](C-05-errors-json-adapter.md), [C-06](C-06-overlay-schema-loader.md), [C-10](C-10-ledger-diff.md), [H-11](../H-testing-observability/H-11-generated-toolkit-tables.md) |
| Gate-conditional | no |
| Decisions | D6, D6b, D118, R24 |
| Sources | [02-butcher.md §2, §5](../../research/02-butcher.md), [19 D118](../../research/19-review-resolutions.md), [08-build-release.md §2](../../research/08-build-release.md), [codex-review.md R24](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The Python legacy butcher (sibling repo `aiogram/butcher`, state in `.butcher/**/entity.json`) is retired for 4.0
(D6). Its successor is a Rust tool, `crates/butcher`, run as `cargo xtask butcher <cmd>`. Every other C task plugs into
the crate layout, the IR types and the committed snapshot format defined here. The IR is the boundary between the
source adapters (HTML, OpenAPI, errors.json) and the emitters. D118 makes it reproducible: each adapter's IR is
committed next to the merged IR, with a manifest.

## Scope

**In:**
- `crates/butcher` (lib + bin) in the workspace created by B-01, and an `xtask` crate with `cargo xtask butcher <cmd>`.
  Register subcommands `fetch`, `build`, `emit`, `diff`, `check`, `import-legacy`. They are stubs that print "not
  implemented", and later tasks fill them in.
- IR types (`ir.rs`): `Ir { header, types, methods, enums, unions, errors }`, `Type`, `Field`, `Method`, `Param`,
  `TypeRef = Prim | Ref | Array | Union`, `Returns`, `Discriminator`, `Enum`, `Constraint`, `Doc` (the source HTML only; plain text and RST are derived at emit time).
  - **Provenance** on every inferred fact: `explicit | heuristic(rule_id) | overlay(file, key)`.
  - **Direction-specific facts** (D118): requiredness, `const` and writability per direction `{request, response}`.
    These are kept even after the D18 twin merge in [C-09](C-09-resolution-passes.md).
  - IR header: `api_version`, `api_date`, `sources: [html, openapi?, errors?]`, `html_only: bool`.
- Stable serialisation: serde JSON with deterministic key order (IR order for entity lists, sorted maps elsewhere),
  2-space indent, trailing newline, LF. No timestamps or absolute paths inside IR files.
- Snapshot layout `butcher/snapshots/<api_version>/`, holding `ir.html.json`, `ir.openapi.json` (when present),
  `ir.errors.json` (when present), `ir.json` (merged) and `manifest.toml`. Only the manifest schema is defined here
  (URLs, fetch time, sha256 per source, butcher version, overlay digest, ledger digest, `html_only`); [C-02](C-02-fetch-provenance.md) writes it.
- `butcher/overlay/` and `butcher/ledger.toml` directories created as empty placeholders, with a README line saying
  what owns them ([C-06](C-06-overlay-schema-loader.md), [C-10](C-10-ledger-diff.md)).
- An `Ir::load(path)` / `Ir::write(path)` round-trip that is byte-identical.

**Out:** adapters (C-03..C-05), overlay (C-06), merge (C-08), emitters (C-12+), the `check` gate (C-23).

## Checklist

- [ ] Add `crates/butcher` and `xtask` to the workspace `Cargo.toml` from B-01; pin dependencies (`serde`, `serde_json`, `toml`, `clap`, `sha2`) in `Cargo.lock`.
- [x] `ir.rs` with the types above, `#[serde(deny_unknown_fields)]` on every struct.
- [x] Provenance enum and direction-specific requiredness/const/writable fields.
- [x] Deterministic writer (`Ir::write`) and loader; a golden round-trip test on a small hand-written IR fixture.
- [x] `manifest.toml` struct + serde, with the fields above.
- [x] `cargo xtask butcher --help` lists every subcommand.
- [x] Clippy restriction lints (`unwrap_used`, `expect_used`, `panic`, `todo`, `unimplemented` = deny) on the crate (08 §5).
- [x] **Decide snapshot retention** (proposed default: commit **only the current API version's** snapshot directory
  and rely on git history as the version archive. Previous snapshots are reachable with `git show <rev>:butcher/snapshots/…`;
  [C-08](C-08-merge-cross-check.md)'s html-only fallback reads the previous snapshot from the same directory before it
  is replaced). Record the choice in Notes and flag it to the owner. The legacy schema alone is 2 MB, so keeping every
  version means about 6 MB per bump.
- [x] Tests (100% coverage of new code where Python; `cargo test` for Rust)

## Acceptance criteria

- `cargo xtask butcher --help` runs on Linux, macOS and Windows CI and lists the 6 subcommands.
- `Ir::load` then `Ir::write` on the fixture is byte-identical, and writing twice yields identical bytes.
- An IR JSON with an unknown key fails to load, with the key path in the error.
- Every IR fact type can carry each of the three provenance kinds (unit test per kind).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep the Python legacy butcher for 4.0 | Prose heuristics drift, CST merge of hand-edited generated files, F821 import bugs, no schema validation | D6 |
| Single IR file without per-adapter IRs | Cannot audit source extraction or replay a disagreement | D118, R24 |
| Commit raw HTML / OpenAPI sources | No explicit license on the schema; raw bundles go to release assets instead | D118, 02 §6 |
| Third adapter on the upstream tdlib generator | Not published (404) | 02 §2 (watch item) |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test -p butcher
cargo xtask butcher --help
```

## Workflow notes

- Input: the workspace skeleton from B-01 (`Cargo.toml`, `crates/aiogram-core`, maturin `pyproject.toml`).
- Output: the IR crate API that C-02..C-10 build on. C-03, C-04, C-05 and C-06 can run in parallel right after this.
- Gate-independent: can start while the B spike is running.

## Notes

- **Snapshot retention (owner, 2026-11-21): the proposed default.** Only `butcher/snapshots/<current>/` is committed;
  git history is the version archive, and `build` for a new API version replaces the directory in the same PR.
- **`sha2` (owner, 2026-11-21):** deferred to C-02, the first plan that computes a digest.

- **Owner question (flagged, not a blocker):** D6b (generator written in Rust) was questioned in
  [codex-review.md §9](../../research/codex-review.md). It compared Rust against Python expertise for parser and overlay
  maintenance, and 19 kept the scope without answering explicitly. `check` needs Python and ruff anyway (C-23), so the
  gain is shared Rust type knowledge with the core crate. The owner should re-confirm D6b before C-03 and C-07 start,
  since those are the costliest tasks. Proceed as planned unless the owner says otherwise.
