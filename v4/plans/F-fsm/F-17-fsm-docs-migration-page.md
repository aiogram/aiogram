# F-17 — FSM & scenes docs and the FSM migration page

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-03](F-03-release-isolation-warn-after.md), [F-06](F-06-redis-storage-legacy-layout.md), [F-07](F-07-mongo-remove-motor-key-validation.md), [F-09](F-09-fsmdata-typed-fsmcontext.md), [F-10](F-10-pydantic-attrs-msgspec-adapters.md), [F-11](F-11-callbackdata-without-pydantic.md), [F-12](F-12-aiogram-types-in-fsmdata.md), [F-13](F-13-scenes-d33.md), [F-14](F-14-typed-scene-data.md), [F-16](F-16-race-suite-314t.md), [I-10](../I-distribution/I-10-diataxis-docs-skeleton.md), [I-12](../I-distribution/I-12-deprecation-machinery-registry-ci.md) |
| Blocks | [J-02](../J-ga/J-02-migration-guide-completion.md) |
| Gate-conditional | no *(the F-11 / F-12 sections are written only if B-13 is a go)* |
| Decisions | D27–D30, D33, D110, D113, D115, PD-04, PD-09, PD-13, PD-22, PD-26 |
| Sources | [04-fsm.md](../../research/04-fsm.md), [18-docs-migration.md §1–§2](../../research/18-docs-migration.md), [README breaking changes 6, 12, 15](../../research/README.md), [11-removals.md §4–§5](../../research/11-removals.md), [plans README §1](../README.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D82: the migration guide is an impact checklist plus per-area pages sharing one registry (PD-13,
`aiogram/_migration/registry.toml`). "FSM & scenes" is one of the per-area pages (18 §2). The F tasks each add their
registry entries and local docstrings; this plan assembles the user-facing pages in the Diátaxis structure from I-10.

## Scope

**In:**
- Concepts page "FSM & typed data" (under `docs/dispatcher/finite_state_machine/` or the I-10 location):
  storages, isolation on by default, `release_isolation`, `isolation_warn_after`, re-entrancy error, release hooks
  (for integrations), the atomicity contract and **lost-update limits** (from F-16), single-loop Redis/Mongo (PD-09),
  multi-process Redis needs `RedisEventIsolation`, stdlib json default and the opt-in core codec (PD-22), typed data
  and adapters, schema evolution.
- Scenes page updates (from F-13/F-14).
- Migration per-area page "FSM & scenes" generated from or cross-linked to the registry entries added by F-01, F-02,
  F-03, F-06, F-07, F-11: `MongoStorage` removal, `CallbackData` pydantic features, isolation default and the
  ask-and-wait recipe, `storage.storage` shape, `StorageKey` slots, single-loop storages.
- Remove the `MongoStorage` autoclass leftovers if F-07 missed any.

**Out:**
- The overall migration guide and impact checklist: J-02.
- Registry machinery and CI: I-12.

## Checklist

- [ ] Concepts page with every topic listed above.
- [ ] Scenes page updates.
- [ ] Migration per-area page; every FSM registry id is referenced exactly once.
- [ ] `uv run --extra docs bash -c 'cd docs && make html'` (or the I-09 import-free build) passes with no new warnings.
- [ ] Changelog fragment in `CHANGES/` (doc).

## Acceptance criteria

- The docs build has no new warnings; every FSM-related registry id appears on the per-area page.
- The lost-update section states, per built-in storage, which operations are atomic and under which isolation.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Separate migration text per plan without the registry | One registry shared with warnings and the checker | D82, PD-13 |

## Validation

```bash
uv run --extra docs bash -c 'cd docs && make html'   # or the I-09 import-free build
make lint
```

## Workflow notes

- Last F plan. Feeds J-02 (migration guide completion).

## Notes
