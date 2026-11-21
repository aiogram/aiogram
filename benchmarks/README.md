# Benchmarks

Dev tooling, not shipped in the sdist or wheel. The inputs are the pinned corpus in
[`corpus/`](corpus/README.md) (A-04). The harness here (A-05) is the one way every 3.x and 4.x
performance change is measured.

```
uv run python -m benchmarks run     --cases <id,...|all> [--out benchmarks/results/<label>.json]
uv run python -m benchmarks compare --base <git-ref> --head <git-ref|WORKTREE> --cases <id,...> [--out …]
uv run python -m benchmarks report  <a.json> [<b.json>]
make bench                                  # run --cases all; extra flags: make bench args="--out …"
```

- **Case ids.** Case ids are the A-04 corpus ids (`update.realistic`, `routing.52-handlers`, …).
  - `all` means every case the harness has.
  - Routing cases run once per variant, e.g. `routing.52-handlers[fsm=on]` and `[fsm=off]`.
  - An id that is in `MANIFEST.toml` but has no case is reported as `missing`.
- **`--loop`.** Picks the event loop: `auto` (the default) uses uvloop when it is importable.
- **Sustained mode.** `--gc-on --duration 30s --interval 1s` switches every selected case to GC-on
  mode: it records throughput per interval and the RSS drift. `memory.update.sustained-gc` always
  runs this way.

## Method

These rules come from 01 §5.6 and codex-review §10. They apply to every case, inside a warm
process:

1. **Warm-up.** 20 calls are made first. For request cases these are 20 real HTTP round-trips.
2. **GC off.** GC is off while sampling, apart from the sustained mode.
3. **Calibration.** The loop count is calibrated so that one sample takes at least 0.2 s.
4. **Samples.** There are **7 samples**. The result file stores the median, the IQR, p5/p95,
   min/max and every raw sample, in µs per call.

**Memory** (R04):

- **tracemalloc:** `tracemalloc` peak and retained bytes of one call, for the decode cases.
- **`memory.update.retained-100k`:** RSS per retained `update.realistic`. A fresh process holds
  100 000 of them, an empty process does the same imports and one decode, and the difference is
  divided by N.
- **`memory.response.retained-child`:** the same method for one `message.chat` kept from each
  decoded `getUpdates` batch of 100.
- **RSS readings:** current RSS comes from `/proc/self/statm` on Linux. Elsewhere it is peak RSS,
  `ru_maxrss`, normalised to bytes. Each result names its `source`.

**Environment.** Every result file records:

- the git commit and the dirty flag (both sides for `compare`);
- the `uv.lock` sha256;
- the Python version, build and free-threaded flag;
- the OS;
- the CPU model, the core counts and the cpufreq governor;
- the event loop;
- the aiogram, pydantic and aiohttp versions;
- the `MANIFEST.toml` sha256, and the id and sha256 of every fixture a case read.

The file format is JSON with `schema = 1`. `report` refuses any other schema.

## `compare`

- **Trees.** `compare` exports each git ref with `git archive` into `.benchmarks/trees/<sha>`. It
  installs each one with `uv sync --locked --no-dev --all-extras` into `.benchmarks/venvs/<sha>`
  and caches both by sha (`.benchmarks/` is gitignored). No git worktree is created.
- **`WORKTREE`.** `--head WORKTREE` is this checkout as it is, with its current interpreter.
- **The same harness on both sides.** Both sides run *this* checkout's harness and corpus, from a
  temporary copy started with `python -I`. Each side imports its own installed aiogram, so a base
  older than the harness can still be measured.
- **Interleaving.** Each side is one warm worker process. The samples are interleaved:
  A, B, A, B, … for 7 each.

How to read a row:

```
case                     unit   base    head   ratio  Δ median  95% CI (bootstrap)  MWU p  head p5..p95
update.realistic           us  88.94   88.36   0.993     -0.7%      [-9.7%, +8.9%]  0.805  83.61..110.46
```

- **Δ median:** `median(head) / median(base) - 1`. Negative means the head is faster.
- **95% CI:** a percentile bootstrap of that ratio, with 10 000 resamples and a fixed seed. When
  the interval contains 0, the run shows no change.
- **MWU p:** an exact two-sided Mann-Whitney U test on the two sets of 7 samples.
- **Thresholds.** `compare` always exits 0. The threshold for each change is in its plan.

Do **not** compare these numbers with the best-of-N `timeit` figures in READMEs, issues or
aiogram_rust. Best-of-N estimates something different from the median of 7. Those figures also
come from another machine and another baseline.

Run `compare --base HEAD --head HEAD` on the same machine first to see that machine's noise. On a
quiet machine the deltas stay within a few percent and the CIs contain 0. A loaded laptop is much
noisier.

## Layout

```
__main__.py              CLI
harness.py               corpus access, case registry, timing loop, statistics, environment, schema
worker.py                the measuring side (in-process for run, a JSON-lines process for compare)
runner.py                run / compare / report, tree export and venvs
memory.py                tracemalloc and RSS probes
adapters/aiogram3.py     everything a case needs from aiogram 3.x; B-02 adds adapters/aiogram4.py
cases/*.py               one setup per corpus id: returns the body to time
results/                 committed result files (A-06)
corpus/                  pinned inputs (A-04)
record/                  trace recorder and redactor (A-04)
```

To add a case, register a setup with `@REGISTRY.case("<corpus id>")` in `cases/`. The setup
receives a `Ctx` (corpus readers that record fixtures, `ctx.adapter`, `ctx.run(coro)` and
`ctx.on_close`) and returns a sync callable or an async function. Call aiogram only through the
adapter.
