# C-11 — `import-legacy`: throwaway Python migration of `.butcher/` YAML

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-06](C-06-overlay-schema-loader.md), [C-07](C-07-fill-dsl.md), [C-10](C-10-ledger-diff.md) |
| Blocks | [C-25](C-25-historical-scenario-tests.md), [C-12](C-12-enums-error-reason-emitter.md), [C-20](C-20-rust-methods-shortcuts-emitter.md), [C-24](C-24-scheduled-online-reextract.md) |
| Gate-conditional | no |
| Decisions | PD-10, D6c, D15, D18, D73, D83, D100, D109 |
| Sources | [02-butcher.md §1, §3, §4](../../research/02-butcher.md), [11-removals.md §1](../../research/11-removals.md), [16-support-policy.md D73](../../research/16-support-policy.md), [plans README PD-10](../README.md), `.butcher/**` (3.x) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The legacy overlays must move to `butcher/overlay/*.toml` once. PD-10 makes the importer a **throwaway Python script**
(`ast` + PyYAML) behind the `cargo xtask butcher import-legacy` shim, which reverses 02 §3's "in Rust". Translating
Python `fill` expressions is a job for `ast`, not for a Rust-side Python parser. 3.x keeps getting Bot API bumps through
legacy butcher for 12 months after 4.0 GA (D73), so the script stays runnable in a **diff mode** until then. That way
shortcuts or defaults added on 3.x are noticed and ported.

Legacy inventory (counted on dev-3.x):

| File kind | Files | Content |
|---|---|---|
| `aliases.yml` | 13 | 189 shortcuts: `method`, `fill` (189), `code` guards (97), `ignore` (38) |
| `default.yml` | 69 | `Default(...)` per param |
| `replace.yml` | 88 | 70 `annotations` (`parsed_type`, `const`, DateTime), 18 `bases`, 3 `returning` |
| `subtypes.yml` | 29 | 27 discriminators, plus the dead `tagged: true` in `MaybeInaccessibleMessage` |
| `unions.yml` | 1 | `sendMediaGroup.media: MediaUnion` |
| `extend.yml` | 1 | `MenuButton` `define` + `clone` |
| `enums/*.yml` | 38 | 20 `multi_parse`, 11 `parse`, 7 `static`, 2 `extract` |
| `entity.json` | 621 | 38 with deprecation markers, 14 with `keep_position` |

## Scope

**In:**
- `scripts/butcher_import_legacy.py` (stdlib + PyYAML, run with `uv run`), plus the `cargo xtask butcher import-legacy
  [--legacy-dir PATH] [--diff]` shim that execs it.
- **Mappings** (target kinds from C-06):
  - `aliases.yml` → `shortcuts/<Type>.toml`. `fill` goes through `ast` into the C-07 grammar (path, `X if C else None` →
    `{expr, when}`, `A.b if A else None` → `A?.b`, zero-arg calls, `None`). `code` asserts become `require`/`forbid`.
    `ignore` is copied. Anything that doesn't fit is written with `handwritten = true` and listed in the report.
  - `default.yml` → `defaults.toml`. The `disable_web_page_preview` / `link_preview_is_disabled` defaults on removed
    params are dropped (11 §1).
  - `replace.yml`:
    - DateTime annotations → `datetime.toml`;
    - `const` and `parsed_type` overrides → `heuristics.toml`, only when the OpenAPI IR doesn't already state the same
      fact; confirmed overrides are dropped and reported;
    - `returning` → `heuristics.toml`;
    - `bases`: `MutableTelegramObject` dropped (D15), `ABC` on `InputFile` dropped (InputFile stays plain Python),
      domain bases (e.g. `ChatFullInfo: Chat`) → `bases.toml` (D83).
  - `subtypes.yml` → `unions.toml` (discriminators). The dead `tagged: true` is reported and not carried.
  - `unions.yml` → `names.toml` union alias. `extend.yml` (`MenuButton`): reported as superseded by the computed common
    fields (C-09) and not carried.
  - `enums/*.yml` → `enums/<Name>.toml`, **except `ContentType`** (removed, 11 §1). `UpdateType`'s `extract` rule is kept.
  - `entity.json` deprecation markers → **not** the ledger (4.0 reset, D6c); C-26 reads them from `.butcher/` on
    dev-3.x itself. `keep_position` is dropped (D100); C-26 takes the positional order from the pinned 3.x venv.
- A report (`target/butcher/import-legacy.md`) with counts per kind, every `handwritten` shortcut with its reason, every
  dropped item with its reason, and the overrides confirmed by the schema.
- **Diff mode** (`--diff --legacy-dir <3.x checkout>/.butcher`): re-import into a temp dir and diff against the
  committed `butcher/overlay/`. It prints legacy additions not yet present in the 4.x overlay and exits non-zero when
  any exist.
- Delete `.butcher/` on **dev-4.x only** in this PR (3.x keeps it, D73).

**Out:** the Rust overlay loader (C-06), the DSL (C-07), the inventory and signature table files (C-26), the CI job
that runs diff mode (C-24 hosts it).

## Checklist

- [ ] Script with the mappings above; output validated by `cargo xtask butcher build` (C-06's loader must accept every generated file).
- [ ] `ast`-based fill translator, with a unit test per expression shape (the C-07 survey table).
- [ ] Report generator.
- [ ] `--diff` mode against a 3.x checkout path.
- [ ] Run it once and commit `butcher/overlay/**` plus the report summary in the PR body.
- [ ] Hand-author the overlay kinds with no legacy source as initial stubs: `methods.toml` (idempotent, every method
  listed explicitly, initially `false` except the reviewed read-only `get*` set. PD-25: the decision must be explicit;
  the importer pre-fills candidates, a human confirms), `display.toml`, `content.toml`, `events.toml`.
  Mark each stub "needs review by <consumer plan>".
- [ ] Delete `.butcher/` on dev-4.x.
- [ ] Tests for the script (pytest under `tests/test_butcher_import/`, 100% coverage of the script; it is deleted together with its tests when D73 full support ends).
- [ ] Changelog fragment / migration-registry entry when user-visible: none (contributor tooling only); the `ContentType` removal entry belongs to C-12.

## Acceptance criteria

- `cargo xtask butcher build` on the imported overlay passes C-06 validation with 0 errors.
- The import report shows all 189 shortcuts imported, with 0 `handwritten` caused by a DSL gap (a DSL gap found here is fixed in C-07's grammar, not marked `handwritten`).
- `ContentType`, `MutableTelegramObject` bases and all 38 entity deprecation markers are absent from the overlay and ledger.
- `--diff` against an unchanged 3.x checkout exits 0. Against a fixture 3.x checkout with one added shortcut, it exits 1 and names it.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Importer written in Rust | One-off; would need a Python-expression parser in Rust | PD-10 (revises 02 §3) |
| Carry 3.x deprecations into the 4.0 ledger | 4.0 reset | D6c |
| Keep `keep_position` | Keyword-only signatures | D100 |
| Port `ContentType` | Removed | 11 §1 |

## Validation

```bash
uv run pytest tests/test_butcher_import
cargo xtask butcher import-legacy --legacy-dir ../aiogram-3x/.butcher
cargo xtask butcher import-legacy --diff --legacy-dir ../aiogram-3x/.butcher
cargo xtask butcher build --offline <bundle>
```

## Workflow notes

- Run it after C-06, C-07 and C-10 are merged. C-26 does not consume this importer's output (it runs on dev-3.x).
- Diff mode is run by the scheduled job (C-24) against `dev-3.x` until 3.x full support ends (D73). Then delete the script, its tests and the shim.

## Notes
