# C-25 — Historical diff and scenario tests (milestone C exit gate)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-08](C-08-merge-cross-check.md), [C-09](C-09-resolution-passes.md), [C-10](C-10-ledger-diff.md), [C-11](C-11-import-legacy.md), [C-20](C-20-rust-methods-shortcuts-emitter.md), [C-21](C-21-generated-tests-emitter.md), [C-23](C-23-check-offline-determinism.md) |
| Blocks | [J-01](../J-ga/J-01-feature-inventory-audit.md), [I-23](../I-distribution/I-23-beta-pre-release.md) |
| Gate-conditional | partial: the `send_copy` and generated-runtime scenarios need C-20/C-21 (gate-conditional); the historical-diff and IR-level scenarios do not |
| Decisions | D118, D109, D18, D107, D6c, R24 |
| Sources | [README milestone C](../../research/README.md), [codex-review.md R24 (Acceptance)](../../research/codex-review.md), [02-butcher.md §2, §4](../../research/02-butcher.md), [19 D118](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Milestone C exits when offline emit is deterministic (C-23) and a fixed set of evolution cases is handled: historical
diffs, a new union, a name collision and an unsupported `send_copy` content (README). R24 also asks for a replayed
HTML/schema disagreement and an input/output mismatch. Telegram keeps no version archive, and raw sources aren't
committed (02 §6), so the historical corpus must be built from what exists. The 3.x repo has **40 commits** of the
legacy-parsed `.butcher/schema/schema.json`, from Bot API 6.4 (2022-12) to 10.4 (2026-11).

## Scope

**In:** `crates/butcher/tests/history/` and `crates/butcher/tests/scenarios/`:
- **Historical replay:** convert each historical `schema.json` (from `git show <rev>:.butcher/schema/schema.json` on
  dev-3.x) into an `ir.html.json`-shaped fixture with a test-only converter (a `--schema-to-ir` mode of the C-11
  Python script). Then run `butcher diff` over consecutive versions and assert the ledger entries and change lists for
  known events: 7.0 `reply_to_message_id` → `reply_parameters`, 7.3 `Chat` fields → `ChatFullInfo`, the
  `KeyboardButtonRequestUser` → `…Users` rename, 10.4 `StoryAreaPosition` removal.
- **Scenarios** (synthetic IR / adapter fixtures):
  1. new discriminated union member and new union → `Unknown…` generated, no failure;
  2. new decoded undiscriminated union without a rule → `check` C004 fails; with a predicate, it passes;
  3. new wire field `raw` (or `bot`) → C003 fails until a rename is configured;
  4. input/output mismatch on a twin (request-only field) → handled per the C-09 decision, with direction facts preserved;
  5. new content kind without a `send_copy` mapping → C005 fails (gate-conditional part);
  6. same-version HTML/schema structural disagreement → `build` fails; an overlay pin resolves it (C-08);
  7. html-only release (OpenAPI one version behind) → `html_only = true`, unchanged entities filled from the previous snapshot;
  8. a field removal → a ledger entry with its due evaluation (C-10);
  9. `ErrorReason` message rewording → the pinned name is kept and the rename reported (PD-24).
- Each scenario also asserts that **no generated output changed** except where expected (snapshot of the emitted-tree hash).

**Out:** runtime forward-compat behaviour (C-19/C-21 tests, E-14).

## Checklist

- [ ] **Decide the historical fixture policy** (proposed default: commit the converted IR fixtures **zstd-compressed** under
  `crates/butcher/tests/history/`. They are derived data, like `entity.json` today, so the 02 §6 license note allows
  them. Raw HTML is never committed). Record it in Notes and flag it to the owner.
- [ ] Test-only `--schema-to-ir` converter (C-11 script) and the fixture generation script.
- [ ] Historical replay test with the named known events.
- [ ] Scenarios 1–9 with their assertions.
- [ ] A milestone-C sign-off section in Notes: the list of passing exit-gate items, with links to the CI runs.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- The historical replay over all 40 versions completes, and the 4 named events produce the expected change lists.
- Scenarios 1–9 each pass, and each fails when its guarding rule is disabled (mutation check).
- Combined with C-23 green on 3 OSes, this satisfies the README milestone C exit gate; record it in Notes.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Wayback-Machine HTML as corpus | Incomplete, third-party, license unclear | 02 §6 |
| Unconditional 3.x parity | 4.0 changes are intended; manifested differences only | R26 |

## Validation

```bash
cargo test -p butcher --test history
cargo test -p butcher --test scenarios
cargo xtask butcher check
uv run pytest tests/test_generated
```

## Workflow notes

- This is the C story's exit gate. J-01 audits it in the feature inventory.

## Notes
