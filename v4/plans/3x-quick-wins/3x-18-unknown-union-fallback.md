# 3x-18 — `Unknown` fallback variant for discriminated unions (optional)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [3x-01](3x-01-polling-poison-isolation.md), 3x-02 (held back) (the poison-update paths exist first), [A-08](../A-contracts/A-08-model-oracle.md), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | — |
| Gate-conditional | no |
| Decisions | D10 (3.x mitigation, "optional, larger change") |
| Sources | [09 #23](../../research/09-3x-quick-wins.md), [10 §1, §3 Layer 1, §5](../../research/10-forward-compatibility.md) |
| Size | L (4–5 days) — **optional**, do only if the owner wants it before 4.0 |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The most common poison update is a new tag in a known union, for example a new `ChatMember` status or a new
`MessageOrigin` type. 3x-01 makes such updates skip instead of stall in polling. A fallback variant goes further: the
update decodes, and the unknown member becomes a generic object, so the rest of the update stays usable. This is
10 Layer 1 in 3.x terms.

## Scope

**In:**
- For every discriminated union that is **decoded**, add a callable `Discriminator` with a fallback tag mapped to a
  generic `UnknownTelegramObject(TelegramObject, extra="allow")` variant, emitted through `.butcher`.
- Unknown enum values on tag-less fields are out (they already decode as `str` thanks to `use_enum_values`; verify).
- The first occurrence of each unknown tag logs one `WARNING` (10 "Visibility").

**Out:**
- The 4.0 `Unknown…` per-union types and `.raw`: C-19 / B-04.
- Request-only unions: no fallback (D107).

## Checklist

- [ ] Ask the owner whether this ships in 3.x. If not, set `Status: dropped` with the answer in Notes.
- [ ] List the decoded discriminated unions (≈25, 01 §1) and their `.butcher` `subtypes.yml`.
- [ ] Decide whether the change lives in the butcher tool or the `.butcher` config (as in 3x-08). Proposed default:
      `.butcher` config if possible; record it in Notes.
- [ ] Generate. Shortcuts on the fallback variant: none.
- [ ] Typing: the union annotation gains `UnknownTelegramObject`. Note it in the changelog: exhaustive `match`
      statements may flag it, which is intended (10 §4).
- [ ] A-08 model oracle: an unknown tag case is "newly supported" in this commit; everything else is invariant.
- [ ] Tests:
  - unknown `ChatMember.status`, unknown `MessageOrigin.type` and unknown `ReactionType` decode, and the field is an
    `UnknownTelegramObject` holding the raw data;
  - the warning is logged once per tag.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.feature.rst` (3.x minor).
- [ ] Migration-registry entry (PD-13, A-11 id block AG47xx): `UnknownTelegramObject` is **3.x-only**; 4.0 replaces it
      with per-union `Unknown…` types (breaking change 9, C-19). Kind `removal-4.0`, replacement "the union's
      `Unknown<Union>` type", `warn_3x.site = "none"`.

## Acceptance criteria

- `update.unknown-tag` from the A-04 corpus decodes without error, and the other fields of the update are intact.
- Regeneration is reproducible (`git diff --exit-code`).
- The `UnknownTelegramObject` registry entry validates against A-11's schema (A-11's `tests/test_migration_registry.py`).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Hand-edit the union modules | Regeneration reverts it | AGENTS.md |
| Fallback for every union, including request-only ones | Request-only unions with primitive members get none | D107 |

## Validation

```bash
uv run --extra cli butcher parse && uv run --extra cli butcher refresh && uv run --extra cli butcher apply all
git diff --exit-code
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
```

## Workflow notes

C-11 must import the result. It doesn't feed any B gate baseline, because the happy path is unchanged.

## Notes

- Coordinator default (reconciliation, K21): `UnknownTelegramObject` gets a `removal-4.0` registry entry (3.x-only type).
