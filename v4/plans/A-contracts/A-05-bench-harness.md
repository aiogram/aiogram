# A-05 — Benchmark harness and method

| Field | Value |
|---|---|
| Status | `done` |
| Story | A — Contracts & baselines |
| Target branch | `dev-3.x` (merged forward to `dev-4.x`, PD-12) |
| Depends on | [A-04](A-04-pinned-corpus.md) |
| Blocks | [A-06](A-06-record-3x-baselines.md), [B-02](../B-spike/B-02-bench-adapter-memory-estimator.md), all measured 3x plans ([3x-01](../3x-quick-wins/3x-01-polling-poison-isolation.md), 03, 04, 05, 06, 07, 08, 09, 11, 12, 13, 14, 17, 23), [3x-03](../3x-quick-wins/3x-03-magicfilter-inline.md), [3x-04](../3x-quick-wins/3x-04-keyboard-builder-add.md), [3x-05](../3x-quick-wins/3x-05-memory-storage-get.md), [3x-06](../3x-quick-wins/3x-06-isolation-lock-pruning.md), [3x-07](../3x-quick-wins/3x-07-drop-model-rebuild-loop.md), [3x-08](../3x-quick-wins/3x-08-butcher-literal-tags.md), [3x-09](../3x-quick-wins/3x-09-json-request-body.md), [3x-11](../3x-quick-wins/3x-11-prebuilt-middleware-chains.md), [3x-12](../3x-quick-wins/3x-12-small-dispatch-costs.md), [3x-13](../3x-quick-wins/3x-13-deserialize-no-ssl-context.md), [3x-14](../3x-quick-wins/3x-14-callback-data-prefix-fast-fail.md), [3x-17](../3x-quick-wins/3x-17-formatting-perf.md), [3x-23](../3x-quick-wins/3x-23-mutation-ledger-warnings.md), [B-00](../B-spike/B-00-freeze-gate-spec.md), [E-21](../E-runtime/E-21-e-exit-gate.md), [F-01](../F-fsm/F-01-thread-safe-memory-storage.md), [F-02](../F-fsm/F-02-isolation-lock-table-default-on.md), [F-04](../F-fsm/F-04-fsm-hot-paths-statefilter.md), [H-06](../H-testing-observability/H-06-tracing-in-executor.md) |
| Gate-conditional | no |
| Decisions | D26, D120, R04, PD-12, codex-review §10, 13 B6 / B24 |
| Sources | [01 §5 (method, item 6)](../../research/01-models.md), [08 §5 Benchmarks](../../research/08-build-release.md), [codex-review §10](../../research/codex-review.md), [13 §1](../../research/13-aiogram-rust-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D120 says each 3.x quick win is measured **against its own baseline**. The B gate compares 4.0 with optimised 3.x
using a defined method (01 §5.6): a warm process, GC off, median of 7, A/B in one session, Linux + uvloop and macOS.
Codex §10 adds:
- store scripts, payload hashes, commit ids, locks, flags, hardware and raw samples;
- report distributions;
- add sustained GC-on runs;
- don't compare best-of-N with median-of-7.

There is no harness in the repository today. 08 §5 leaves the tool open ("pytest-codspeed or asv").

## Scope

**In.** Proposed layout and CLI (record any change in Notes; plans cite this CLI):

```
benchmarks/__init__.py, __main__.py
benchmarks/cases/{decode,dispatch,request,utils,fsm,imports}.py   # case functions keyed by A-04 input ids
benchmarks/results/<label>.json                                    # committed results (A-06)
uv run python -m benchmarks run     --cases <id,...|all> --out benchmarks/results/<label>.json
uv run python -m benchmarks compare --base <git-ref> --head <git-ref|WORKTREE> --cases <id,...>
uv run python -m benchmarks report  <a.json> <b.json>
```

- **Method.** Per case:
  - warm-up (20 iterations, or the "20 real requests first" rule for request paths);
  - `gc.disable()`, `timeit`-style loops calibrated to ≥ 0.2 s;
  - **7 repeats**, storing the median, IQR and all raw samples;
  - an optional sustained GC-on mode (`--gc-on --duration 30s`) that reports throughput and RSS drift.
- **Memory:**
  - `tracemalloc` (peak and retained) per case;
  - RSS from a fresh subprocess holding N retained objects (100k updates for decode, R04);
  - a "retained child from a 100-update batch" case;
  - RSS read via `/proc/self/statm` on Linux and `resource.getrusage` delta in a fresh process on macOS.
- **Environment capture** in every result: git commit (and whether the tree is dirty), `uv.lock` hash, Python
  version and build (incl. free-threaded flag), OS, CPU model / cores, governor if readable, uvloop on/off, aiogram
  and pydantic versions, corpus `MANIFEST.toml` hash.
- **`compare`:** builds or uses two git worktrees (`git worktree add`), installs each with `uv sync --locked` into
  its own venv, runs the same cases interleaved A/B/A/B in one session, and prints the median delta with
  Mann-Whitney U or bootstrap CI (stdlib only). Exit code 0 always; thresholds live in the plans.
- **Side adapter:** cases import aiogram through a thin 3.x adapter (`model_validate_json`, `feed_update`, …). B-02
  adds the 4.0 adapter and the memory estimator for Rust objects.
- `make bench` target (`uv run python -m benchmarks run --cases all`).
- A non-blocking CI job (`workflow_dispatch` + weekly) running `run` on Linux and uploading the JSON as an artifact.
  `make lint-workflows` applies.

**Out:**
- Recording the official baselines: A-06.
- The 4.0 adapter: B-02.
- Release-cost metrics (build time, wheel size): I-06.

## Checklist

- [x] Decide the tool. Proposed default: a **stdlib harness** (as above). pytest-codspeed counts instructions and
      can't express the memory gate; asv adds a framework for what ~300 lines do. Codspeed may be added later for PR
      regression only. Record the choice in Notes and flag it to the owner (08 §5 left it open).
- [x] Add a case function for every A-04 input id that plans cite (see the 3x plans' Validation sections), with
      ids exactly as in A-04.
- [x] Implement `run` / `compare` / `report` and the JSON schema (versioned, `schema = 1`).
- [x] Add a self-test (`tests/test_benchmarks_harness.py`) using a tiny fake case:
  - repeats = 7;
  - environment fields present;
  - `compare` detects a deliberately slowed head (an injected `time.sleep` in a fake case);
  - JSON round-trips.
- [x] Add `make bench` and the CI job; run `make lint-workflows`.
- [x] Write a "Benchmarks" section in `benchmarks/README.md`: method, CLI, how to read `compare`, and "don't
      compare with README best-of-N numbers".
- [x] Changelog: none (dev tooling). Use the `skip news` label.

## Acceptance criteria

- `uv run python -m benchmarks compare --base HEAD --head HEAD --cases update.realistic` reports a median delta
  within ±3%, and its CI includes 0 (noise calibration). Record the numbers in Notes, on macOS and Linux.
- The self-test catches the injected slowdown.
- A results file contains raw samples and every environment field listed above.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Best-of-N `timeit` (README method) | A different estimator from the gate's median of 7 | codex-review §10, 01 §5.6 |
| Harness on `dev-4.x` only | D120 needs it for 3.x PRs now | PD-12 |
| Compare against aiogram_rust numbers | Different machine and baseline | 13 §1 |

## Validation

```bash
uv run pytest tests/test_benchmarks_harness.py -q
uv run python -m benchmarks compare --base HEAD --head HEAD --cases update.realistic,routing.52-handlers
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
make lint-workflows
```

## Workflow notes

- **Outputs:** the CLI and JSON schema used by every measured plan. B-02 extends the harness with a 4.0 adapter and
  Rust memory accounting; I-06 / I-05 may reuse the CI job.
- Lands before any measured 3x plan merges. Those plans can be developed in parallel and measured once A-05 is in.

## Notes

- Tool: a stdlib harness, the proposed default (owner, 2026-11-21, plan approval). No new dependency. pytest-codspeed
  can still be added later for PR-regression only.
- `compare` exports each ref with `git archive` into `.benchmarks/trees/<sha>` and installs it with
  `uv sync --locked --no-dev --all-extras` into `.benchmarks/venvs/<sha>`, both cached by sha. It does not use
  `git worktree add` (owner, 2026-11-21). Both sides run the invoking checkout's harness and corpus from a temporary
  copy under `python -I`, so a base older than A-05 can still be measured.
- The memory cases got three appended corpus ids (owner, 2026-11-21): `memory.update.retained-100k`,
  `memory.response.retained-child` and `memory.update.sustained-gc`. RSS comes from a fresh subprocess, with an
  empty-process baseline subtracted (B-02:45). Current RSS is read from `/proc/self/statm` where there is one; elsewhere
  peak RSS from `ru_maxrss`, normalised to bytes. On macOS `memory.response.retained-child` (N = 1000) is noisy, because
  the peak is dominated by the batch decode. Its tracemalloc figure is the precise one.
- Layout as proposed, plus these modules:
  - `harness.py` (registry, timing, statistics, environment, schema);
  - `worker.py` (the measuring side);
  - `runner.py` (run / compare / report);
  - `memory.py`;
  - `adapters/{__init__,aiogram3}.py`.

  B-02 adds `adapters/aiogram4.py`.
- CLI additions that no plan needs to cite:
  - `compare --out`;
  - `--interval` for the sustained mode (default 1 s; `--duration` defaults to 30 s, so B-02 can pass 5m/10s);
  - `--loop auto|asyncio|uvloop` (auto = uvloop when importable);
  - `report` also takes a single file.
- Results include p5/p95 and the id + sha256 of every fixture a case read (B-02:74, B-02:88). Variants are labelled
  `routing.52-handlers[fsm=on]`. Inputs that 3.x rejects (`on_3x` other than `ok`) have no case and report `missing`.
- Request cases make a real round-trip through `AiohttpSession` to a local aiohttp server in the worker's loop. The
  server answers with the pinned `response.sendMessage` envelope. The figure is client + server.
- Noise calibration on macOS (M2 Pro, CPython 3.15.2, uvloop, load average about 5), from
  `compare --base HEAD --head HEAD`:
  - `update.realistic`: +0.4%, 95% CI [-1.1%, +1.2%];
  - `routing.52-handlers[fsm=on]`: -1.3%, CI [-9.1%, +5.0%];
  - `routing.52-handlers[fsm=off]`: -1.7%, CI [-14.5%, +7.6%].

  The routing CIs are wide because 3.x resolves `F.text` filters in the thread pool (3x-03).
- Linux noise calibration is pending for A-06. A `workflow_dispatch` run needs the workflow on the default branch, so
  the Linux numbers come from the first run after merge.
