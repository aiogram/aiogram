# C-23 — `butcher check`, offline determinism and the PR CI job

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-10](C-10-ledger-diff.md), [C-12](C-12-enums-error-reason-emitter.md), [C-13](C-13-reexport-modules.md), [C-15](C-15-bot-methods-emitter.md), [C-16](C-16-router-observers-update-tables.md), [C-17](C-17-utility-signature-emitter.md), [I-05](../I-distribution/I-05-pr-ci-structure-caching-coverage.md) |
| Blocks | [C-25](C-25-historical-scenario-tests.md), [I-08](../I-distribution/I-08-contributor-workflow.md) |
| Gate-conditional | no (Rust emitters C-18..C-20 plug in when they land) |
| Decisions | D118, D109, D85/D107, PD-25, R24, R28 |
| Sources | [02-butcher.md §5 (`check`), §5.2 (formatting)](../../research/02-butcher.md), [19 D118](../../research/19-review-resolutions.md), [08-build-release.md §5](../../research/08-build-release.md), [14-testing.md §3](../../research/14-testing.md), [codex-review.md R24](../../research/codex-review.md), [plans README PD-25](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Milestone C's exit gate is "offline emit deterministic". `check` is the CI gate. It regenerates everything from the
**committed** IR, overlay and ledger with no network, and fails on any diff. It also hosts the semantic rules that stop
a Bot API bump from silently misgenerating behaviour (R24 acceptance).

## Scope

**In:** `cargo xtask butcher check [--fix]`:
- **Regenerate and diff:** emit every registered emitter into a temp tree from `butcher/snapshots/<current>/ir.json` plus
  overlay plus ledger, then compare with the working tree. Any difference fails, with a unified diff. `--fix` writes the
  output. The network is never used (enforced: the HTTP client isn't linked into the `check` code path).
- **Rules** (each with an id, a message and a test):
  - `C001` overlay or ledger validation errors (C-06, C-10);
  - `C002` structural or heuristic disagreements in the snapshot's report (C-08);
  - `C003` name collision without a rename (C-09, D109);
  - `C004` decoded undiscriminated union without a tag or predicate (D85/D107);
  - `C005` content kind without a `send_copy` mapping (C-20);
  - `C006` method without an explicit `idempotent` decision (PD-25);
  - `C007` retired, not reused (fake coverage is H-11's pytest guard; C-06 has no fake marks);
  - `C008` update type without an `events.toml` entry (C-16);
  - `C009` ledger entries that are due (C-10; a report, failing only with `--strict-due`, R28);
  - `C010` change in the computed D18 twin list (C-09);
  - `C011` `ErrorReason` member without a pin (PD-24).
- **Determinism:** emit twice in one run and compare bytes. Output is LF-only on every OS. `ruff format` comes from the
  locked ruff version (see Decide item) and `prettyplease` from `Cargo.lock`.
- **CI job** (`.github/workflows/` job `butcher-check`, added by this plan into I-05's workflow structure, which
  lands first): Linux, macOS and Windows; network
  disabled for the step; runs `check` from a clean checkout.

**Out:** the online re-extract (C-24); the wheel and stubtest jobs (I-04, I-05).

## Checklist

- [ ] Emitter registry (every `emit/*` module registers its output root).
- [ ] Regenerate-and-diff with `--fix`.
- [ ] Rules C001–C011, each with a fixture test that triggers it.
- [ ] **Decide how the formatter version is pinned** (proposed default: `check` runs `uv run --locked ruff format` so
  ruff comes from `uv.lock`, and refuses to run if the ruff version differs from a `butcher/emit.toml` pin. A ruff bump is
  a separate PR that re-emits). Record it in Notes and flag it to the owner.
- [ ] `butcher-check` CI job on 3 OSes with the network off, added into I-05's structure; `make lint-workflows`
  (zizmor) passes.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- A clean checkout passes `cargo xtask butcher check` on Linux, macOS and Windows with no network.
- Editing one generated file by hand fails `check` with a diff that points to that file.
- Each rule C001–C011 has a fixture that fails `check` with its id.
- Two consecutive `emit` runs produce byte-identical trees (hash of the tree compared).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| CI fetching live sources | Mutable, staging availability | D118 |
| Generated files with merge regions | Fully regenerated; hand code in `*_ext.*` | 02 §5.1 |
| Unpinned formatter | Non-deterministic output | 02 §5.2 |
| Auto-dropping due ledger entries | Explicit due-removal decision | R28 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test -p butcher check
cargo xtask butcher check
rtk proxy make lint-workflows
```

## Workflow notes

- Every later emitter (C-14, C-18..C-22) registers itself and its outputs become covered automatically.
- I-05 folds the job into the PR CI structure.

## Notes

- Coordinator default (reconciliation, K18): this plan depends on I-05 and adds the `butcher-check` job into I-05's
  structure; I-05 no longer depends on C-23 or carries a placeholder job.
