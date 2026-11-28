# C-04 — OpenAPI 3.2 adapter

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-01](C-01-crate-xtask-ir-snapshot.md) |
| Blocks | [C-08](C-08-merge-cross-check.md) |
| Gate-conditional | no |
| Decisions | D6a, D18, D118 |
| Sources | [02-butcher.md §2, §3 item 7](../../research/02-butcher.md), [01-models.md §3.1](../../research/01-models.md) (int widths), [05-network.md §2](../../research/05-network.md), [19 D118](../../research/19-review-resolutions.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`<host>/bots/api.json` (OpenAPI 3.2; corefork, 10.3 on 2026-11-16) carries facts the HTML cannot express:
- 23 discriminator mappings, 541 consts, 113 enums;
- `int32`/`int64`/`double` (217 int64 fields);
- constraints;
- 34 multipart bodies with `encoding`;
- return types through `mediaTypes`;
- request vs response direction, and the 74 `Input*`/output pairs.

When both sources have the same version, schema facts are primary and the HTML is a structure check (02 §2).

## Scope

**In:** `crates/butcher/src/sources/openapi.rs` (`serde_json`), producing `ir.openapi.json`:
- `components.schemas` → `Type`/`Field`; `paths` → `Method`/`Param` (request body schema), with `Returns` from the
  success response `mediaTypes` (e.g. `MessageOrTrueResult`);
- discriminators (`propertyName` + `mapping`) → `Discriminator`; `oneOf` without a discriminator → undiscriminated union (12 today);
- `enum` / `const` → IR enums and consts (both `explicit`);
- `format: int32 | int64 | double` → IR primitive widths;
- constraints (`minLength`, `maxLength`, `minimum`, `maximum`, `maxItems`, `pattern`) → `Constraint`;
- multipart `encoding` per field → method encoding metadata (consumed by C-20 and D-08);
- **direction**: a schema reachable from request bodies, from responses, or both. Requiredness, const and writability
  are recorded per direction (D118). `Input*` schemas stay separate entities here; the D18 merge happens in C-09;
- error responses on paths, kept as metadata (the catalogue itself is C-05);
- schema `info.version` → IR header `api_version`.

**Out:** errors.json (C-05), merging and the D18 twin merge (C-08, C-09).

## Checklist

- [ ] Loader for OpenAPI 3.2 (`$ref` resolution within the document; external refs are an error).
- [ ] Types, fields, methods, params and returns mapping.
- [ ] Discriminated and undiscriminated unions.
- [ ] Enums, consts, int widths, constraints.
- [ ] Multipart `encoding` metadata.
- [ ] Direction reachability pass (request / response / both) with per-direction requiredness and const.
- [ ] Unknown OpenAPI keywords: warn once per keyword, never silently drop a structural keyword (`oneOf`, `allOf`, `discriminator`, `required`).
- [ ] Fixture tests with small hand-written OpenAPI excerpts (same fixture policy as C-03).
- [ ] Count assertions against a cached 10.3 `api.json` (behind `BUTCHER_LIVE=1`): 23 discriminators, 541 consts, 113 enums, 34 multipart bodies, 74 `Input*` pairs.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- The live-gated count test matches the counts above for the 10.3 schema.
- `ChatPermissions` and `InputChatPermissions` have per-direction requiredness recorded (fixture test).
- An `allOf` / `oneOf` shape the adapter can't map fails with the schema path.
- Output is byte-identical across two runs.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| OpenAPI as the only source | Lags the live API on staging | 02 §2 |
| Merge `Input*` twins inside the adapter | Loses direction facts; the merge is a resolution pass (C-09) | D18, D118 |
| Interpreting the schema at runtime (pydantic-core style) | Types are fixed per release and we own the generator | 08 §1 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test -p butcher openapi
BUTCHER_LIVE=1 cargo test -p butcher openapi_counts -- --ignored
```

## Workflow notes

- Parallel with C-03, C-05 and C-06. C-08 consumes `ir.openapi.json`. D-08 relies on the `encoding` metadata via C-20.

## Notes
