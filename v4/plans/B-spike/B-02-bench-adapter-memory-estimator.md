# B-02 — Bench harness 4.0 adapter + memory estimator

| Field | Value |
|---|---|
| Status | `todo` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-00](B-00-freeze-gate-spec.md), [B-01](B-01-crate-maturin-skeleton.md), [A-04](../A-contracts/A-04-pinned-corpus.md), [A-05](../A-contracts/A-05-bench-harness.md), [A-06](../A-contracts/A-06-record-3x-baselines.md) |
| Blocks | [B-12](B-12-dispatch-harness.md), [B-13](B-13-gate-run-and-decision.md) |
| Gate-conditional | no |
| Decisions | D26, D104, R04, PD-12 |
| Sources | [01-models.md §5](../../research/01-models.md), [13-aiogram-rust-review.md §1, B6, B24](../../research/13-aiogram-rust-review.md), [codex-review.md R04, §10](../../research/codex-review.md), [08-build-release.md §5](../../research/08-build-release.md), [19 R04](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

A-05 provides the benchmark harness, and A-06 provides the recorded 3.x baselines (stock and the optimised-3.x tag),
authored on `dev-3.x` and merged forward (PD-12). The gate also needs a **4.0 side**: workloads that drive
`aiogram._core`, the warm-process protocol of 01 §5.6, and a memory estimator that sees native Rust allocations,
which tracemalloc cannot (R04). This plan **extends** A-05. It doesn't fork or duplicate it.

## Scope

**In:**
- **4.0 adapter.** An adapter in the A-05 harness exposing the same workload names as the 3.x side and reading
  workload ids, inputs and gating from `benchmarks/b_gate/gate.toml` (B-00).
  - Workloads register as the spike lands (B-04..B-12).
  - A gated workload with no 4.0 implementation reports `missing`, never `skipped`, and B-13 treats `missing` as a
    failure.
- **Warm protocol (01 §5.6, 13 B6).**
  - A local fake Bot API (aiohttp server in the harness process) answers the pinned `sendMessage` / `getUpdates`
    responses.
  - 20 round-trips run before measurement, so `Py` objects have been dropped while detached and pyo3's reference
    pool is armed.
  - GC is off for the micro-benchmarks, median of 7, A/B in one machine session, uvloop on Linux.
- **Memory estimator (B-00 choice; default below).**
  - A cargo feature `alloc-stats` that installs a counting `#[global_allocator]` wrapper around the system
    allocator. It exposes `_core._alloc_stats() -> (live_bytes, peak_bytes)`, is built only for bench runs and is
    off in release wheels.
  - Fresh-subprocess peak-RSS measurement through `resource.getrusage` (stdlib, no new dependency): retain N decoded
    updates, subtract an empty-subprocess baseline, divide by N.
  - tracemalloc reported next to both.
- **Memory workloads (R04).** Untouched retained; typical access; fully materialised; `.raw` / `to_dict()` use; one
  `Message` child retained from a 100-update batch; GC-on sustained parse/drop with RSS sampled every 10 s.
- **Run record (codex §10).** Each run stores the commit ids (both sides), `uv.lock` / `Cargo.lock` sha256, fixture
  sha256 (from the A-04 manifest), rustc / pyo3 / maturin versions, build profile and flags, CPU model, core count,
  OS and raw samples, as JSON under `benchmarks/results/b-gate-<date>-<host>.json` (A-05 results directory).
- **Baseline freeze.** The optimised-3.x side (A-06 tag) is run once and stored after B-00 sign-off, so later
  baseline drift can't move the target.

**Out:**
- The harness core, fixture loading and the 3.x workloads (A-05).
- Recording 3.x baselines in general (A-06).
- The dispatch workload (B-12 adds it).
- Gate judging (B-13). CI regression benchmarking with codspeed/asv (I-05).

## Checklist

- [ ] Read the A-05 harness API and add the 4.0 adapter as a sibling of the 3.x adapter (same workload names).
- [ ] Load workload definitions and gating from `gate.toml`; report `missing` for unimplemented gated workloads.
- [ ] Add the in-harness fake Bot API and the 20-request warm-up; assert that the warm-up ran before every sample
  set.
- [ ] Add the `alloc-stats` cargo feature and `_core._alloc_stats()`; `make bench` builds it with
  `--features alloc-stats`.
- [ ] Add the subprocess peak-RSS estimator and its empty-baseline subtraction; check the estimator against a known
  allocation (e.g. retaining 100 MB of `bytes` reads as 100 MB ± 5%).
- [ ] Add the memory workloads listed in Scope, including the GC-on sustained run, which fails on monotonic RSS
  growth > 5% over its last 5 minutes.
- [ ] Add the run record and raw-sample storage; add a `report` command printing ratios, absolute µs/bytes and p5/p95.
- [ ] Freeze the optimised-3.x baseline run after B-00 sign-off (commit the result JSON).
- [ ] Tests: unit tests for the estimator arithmetic, `gate.toml` → workload resolution, `missing` reporting and the
  run-record schema (100% of new Python).
- [ ] No changelog or registry entry (bench only).

## Acceptance criteria

- `make bench && uv run python -m benchmarks run --cases all --out benchmarks/results/b-gate-4x.json` runs on the
  4.0 side (the adapter reads `benchmarks/b_gate/gate.toml`), and prints `missing` for every gated A-04 case id whose
  spike code isn't merged yet.
- The 100 MB `bytes` self-check reads 100 MB ± 5% under both the RSS estimator and `_alloc_stats()` (for a Rust-side
  100 MB `Vec`).
- A committed optimised-3.x baseline result JSON exists, with its run record, for Linux and macOS.
- Each result JSON names every fixture by A-04 id + sha256.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| A second, B-only harness | Duplicates A-05; differential results must share one harness | PD-12 |
| tracemalloc alone | Misses Rust allocations | R04 |
| psutil for RSS | A new dependency for what `resource.getrusage` in a fresh subprocess does | AGENTS.md "no new dependencies for small tests" |
| Comparing with best-of-N historical numbers | A different estimator | codex §10 |
| Benchmarks in a cold process | The pyo3 reference-pool cost only shows in a warm process | 13 B6, 01 §5.6 |

## Validation

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets --features alloc-stats -- -D warnings
cargo test --workspace
make bench
uv run python -m benchmarks run --cases update.realistic,response.getUpdates.100 --out benchmarks/results/b-gate-smoke.json
uv run pytest tests/test_core
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: A-04 manifest and fixtures, the A-05 harness, the A-06 optimised-3.x tag, `gate.toml` (B-00).
- Outputs: the 4.0 adapter, which B-04..B-12 register workloads into; the memory estimator; the frozen baseline JSON
  that B-13 judges against.
- Can run in parallel with B-03/B-04 once B-00 and B-01 are done.

## Notes
