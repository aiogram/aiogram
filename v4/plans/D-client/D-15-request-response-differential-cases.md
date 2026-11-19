# D-15 — Request/response differential cases with difference manifests (D exit gate, part 1)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [A-07](../A-contracts/A-07-differential-framework.md), [A-09](../A-contracts/A-09-request-oracle.md), [D-07](D-07-rust-encoder-json.md), [D-08](D-08-rust-encoder-multipart.md), [D-09](D-09-response-decoder.md), [D-11](D-11-session-on-new-codec.md), [D-12](D-12-custom-session-hook-compatibility.md), [D-13](D-13-raw-bot-call-raw-method.md) |
| Blocks | [H-16](../H-testing-observability/H-16-fake-fidelity.md), [J-01](../J-ga/J-01-feature-inventory-audit.md) |
| Gate-conditional | yes (assumes the milestone B gate passes, D104; re-validate after B-13) |
| Decisions | R26, B8, PD-11, PD-12, PD-29 |
| Sources | [19 §2 R26](../../research/19-review-resolutions.md), [codex-review.md R26](../../research/codex-review.md), [13-aiogram-rust-review.md §3 B8](../../research/13-aiogram-rust-review.md), [08-build-release.md §5](../../research/08-build-release.md), [14-testing.md §3](../../research/14-testing.md), [README milestone D](../../research/README.md), [plans README §1](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Milestone D's exit gate: "request/response differential cases with difference manifests (R26), hook compatibility".
A-07 provides the differential harness framework (two venvs, canonical traces, poison control, manifest format) and
A-09 the request/response oracle on the pinned external 3.x venv (PD-12). This plan **adds the 4.0 side and the
cases**; it adds no new harness framework.

R26: each case is **invariant**, **approved difference** (decision id + narrow assertion) or **newly supported**;
intended 4.0 changes are approved differences, not snapshot exclusions. Cover constructors, defaults, Unknown paths,
custom sessions and wrappers, not only happy-path JSON.

## Scope

**In:**
- 4.0 adapter for the A-09 request oracle: canonical request trace from `encode_request` (method name, fields as JSON
  values regardless of form vs JSON body, files as `(field, filename, sha256)`, attachment names canonicalised).
- 4.0 adapter for the response oracle: canonical outcome from `decode_response` (result wire dict via `to_dict()`, or
  exception class + `reason` + message + `retry_after`/`migrate_to_chat_id`).
- Cases (in the A-04 corpus / A-09 case files): every method family with defaults, nested `Default`, files (top-level,
  media groups, stickers), DateTime/timedelta, extras (D99), raw calls (D-13) vs generated methods, custom-session
  subclasses (D-12), error envelopes for each status branch, unknown union tags / enum values, malformed results,
  `getUpdates` batches with one poisoned update, recorded traces (redacted, with provenance) and hand-curated wire
  fixtures.
- Manifest entries — at least these approved differences:

  | Difference | Decision | Narrow assertion |
  |---|---|---|
  | JSON body instead of urlencoded form when no files | 05 §2.1 | same canonical fields; content type differs |
  | Deterministic attachment names | D-08 Decide item | canonicalised names equal |
  | Naive datetime on Windows = local time (3.x: UTC) | PD-11 | only on `win32` cases |
  | `RestartingTelegram` → `TelegramServerError` | 11 §2 | class differs, message equal |
  | Ledger-reset fields/params removed | 02 §4, README #8 | field absent / `TypeError` |
  | Flat `link_preview_*` defaults removed | 11 §2 | constructor `TypeError` |
  | Unknown tags decode instead of raising | D10, D107 | 4.0 returns `Unknown…`; 3.x `ClientDecodeError` (newly supported) |
  | Poisoned update isolated | D10 | other updates equal |
  | Session JSON hooks ignored on the wire | PD-08 | body identical to default session |

- `timedelta` cases are **invariant** (both sides `now + delta`, PD-11) under a frozen clock.
- Poison control run on the 4.0 side (A-07 mechanism) must report mismatches.

**Out:**
- Harness framework, manifest schema → A-07. 3.x oracle → A-09. Model decode/dump differential → B/C (A-08).
  Routing differential → E-21 (A-10). Fake-fidelity replay → H-16 (reuses these traces).
- A "Rust vs Python fallback encoder" leg (08 §5): there is no Python fallback encoder (D1); see D-12 Notes.

## Checklist

- [ ] 4.0 request adapter (canonical trace).
- [ ] 4.0 response adapter (canonical outcome).
- [ ] Case set listed above added to the corpus, each classified in the manifest.
- [ ] Approved-difference entries with decision ids and narrow assertions.
- [ ] Recorded traces: redacted (no token, H-02 regex or D-03 helper), provenance fields per A-07 schema.
- [ ] Poison control passes (i.e. detects the injected mismatch).
- [ ] CI job runs the harness on Linux and macOS (Windows for the `win32`-only cases).
- [ ] Decide which 3.x tag the oracle pins for D (proposed default: the A-06 "optimised" tag that includes 3x-09 /
      3x-10, so JSON-body and webhook-reply differences shrink to content type only) — record in Notes and flag to
      owner.

## Acceptance criteria

- The harness run reports zero unclassified differences across all D cases.
- Every approved difference names a decision id and asserts only the stated property.
- The poison control produces ≥1 mismatch and the run fails without it.
- Recorded traces contain no token substring (scanned in CI).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Require unconditional 3.x parity | 4.0 changes serialization on purpose | R26 |
| Broad snapshot exclusions | Hide unintended changes | R26 |
| In-tree 3.x reference path | Oracle is an external pinned venv | PD-12 |
| A new harness framework for D | A-07/A-09 exist | coordinator scope |

## Validation

```bash
make dev
uv run pytest tests
# then run the A-07 harness entry point for the client suite against the pinned 3.x venv
# (the exact command is defined by A-07; copy it into the PR description)
make lint
```

## Workflow notes

- Inputs: A-07 framework, A-09 oracle, D-07..D-13 implementations.
- Outputs: classified client cases for J-01's inventory; traces reused by H-16.

## Notes
