# B-00 — Freeze the gate spec

| Field | Value |
|---|---|
| Status | `todo` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [A-04](../A-contracts/A-04-pinned-corpus.md), [A-05](../A-contracts/A-05-bench-harness.md), [A-06](../A-contracts/A-06-record-3x-baselines.md) |
| Blocks | [B-02](B-02-bench-adapter-memory-estimator.md), [B-04](B-04-spike-type-set.md), [B-12](B-12-dispatch-harness.md), [B-13](B-13-gate-run-and-decision.md) |
| Gate-conditional | no |
| Decisions | D26, D104, D121, R01, R04, PD-03, PD-30 |
| Sources | [README roadmap, B row](../../research/README.md), [01-models.md §5](../../research/01-models.md), [13-aiogram-rust-review.md §1, §5](../../research/13-aiogram-rust-review.md), [codex-review.md R01, R04, §10](../../research/codex-review.md), [19](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The B gate is binding and has no pre-committed fallback (D104). R01 requires the numerical and semantic gates to be
frozen **before** the spike, and codex §10 forbids relaxing a threshold after a failed run. The README row is terse
and leaves several things undefined: per-workload vs aggregate ratios, what "first access" is compared to, how memory
is measured, which child is retained, and whether encode/shortcut/pickle numbers gate anything. A gate that can be
read two ways will be read the convenient way after the fact. This task writes the one spec that B-02 measures
against and B-13 judges by, and has the owner sign it off.

## Scope

**In:**
- A machine-readable spec `benchmarks/b_gate/gate.toml`, placed next to the A-05 harness (that location is the default):
  workloads, pinned input ids from the A-04 manifest, estimator, platforms, thresholds, and gated/informational flags.
- A short rationale `benchmarks/b_gate/README.md` that maps every entry to its research source.
- The spike type list, as the closure of the types used by the gated A-04 fixtures. It is consumed by B-04.
- Owner sign-off, recorded in *Notes* with the date.

**Out:** running anything (B-02, B-13), the harness itself (A-05, B-02), and the baselines (A-06).

## Checklist

- [ ] Copy the binding thresholds verbatim from the README B row: parse ≥3×, memory ≥4× (incl. accessed trees and a
  child retained from a batch), first access ≤2×, warm access ≤1.6×, end-to-end dispatch no slower than optimised 3.x,
  `getUpdates` batch + `sendMessage` response paths (B24), cache/GC/teardown tests pass. Platforms: Linux + macOS,
  warm, pyo3 ≥0.30. Baseline: the A-06 **optimised-3.x tag**, never an unmerged optimisation (codex §10).
- [ ] Decide how parse ratios are scoped (proposed default: **each** gated decode workload passes ≥3× on its own on
  each platform: realistic update, plain-text update, `getUpdates`×100 through the response envelope, `sendMessage`
  response). Record in Notes and flag to owner.
- [ ] Decide what first access is compared to (proposed default: native first read of a fixed access path, which
  includes wrapper materialisation, vs pydantic read of the same path on an already-parsed object, ≤2×). Fixed path:
  `update.message.text`, `.message.from_user.id`, `.message.chat.id`, `.message.entities[0].type`. Record and flag.
- [ ] Define warm access as the same path read again on the same view, ≤1.6×. D26 says "warm raw access"; the spec
  must say this means a plain attribute getter, not `.raw`.
- [ ] Decide the memory estimator (proposed default: per-update bytes = peak-RSS delta of a fresh subprocess holding
  100k decoded updates (`resource.getrusage`, stdlib) divided by 100k. The counting allocator from B-02 and
  tracemalloc are reported next to it, never alone, because tracemalloc can't see Rust allocations, R04). Record and
  flag.
- [ ] Decide the memory workloads and their gating (proposed default: **gated ≥4×**: untouched retained updates,
  "typical access" trees (the first-access path above), and a retained child. **Informational**: fully materialised
  tree, `.raw` / `to_dict()` use, and a GC-on sustained parse/drop run, which must show no growth over 10 min).
- [ ] Decide which child is retained (proposed default: one `Message` kept from a 100-update `getUpdates` batch, the
  rest dropped. A retained `User` is informational: per-update byte copies (19 §3.3) plus the shared `Arc` tree make
  ≥4× unlikely for tiny children, R04). Record and flag.
- [ ] Decide what "no slower" means for dispatch (proposed default: native median ≤ baseline median **and** the upper
  95% bootstrap bound of the ratio ≤ 1.05). Workload: A-10's pinned realistic router, run by B-12 with the same 3.x
  dispatcher on both sides and no rejectors. Record and flag.
- [ ] Record how 01 §5.4's "with `routing_keys()`" is interpreted: `routing_keys()` exists (B-05) and is benchmarked
  as informational; the gate dispatch runs **without** compiled rejectors, so routing gains (E-09) are not credited to
  the model layer.
- [ ] Decide the gating of the other benchmarks in 01 §5.2 (proposed default: informational, with two hard floors.
  (a) The `SendMessage` encode is not slower than the 3x-09 JSON body on the same input. (b) Re-mount is O(1): time is
  flat across the plain-text and realistic updates. `to_json` / `to_dict`, pickle round-trip, the shortcut up to the
  coroutine and registered-subclass instantiation are informational.) Record and flag.
- [ ] Decide the estimator and run protocol: median of 7 runs, GC off, A/B in one machine session, raw samples kept,
  p5/p95 reported. Best-of-N historical numbers are never compared with it (codex §10). Warm-up is 20 `sendMessage`
  plus `getUpdates` round-trips through aiohttp against the harness's local fake Bot API (proposed reading of 01 §5.6
  "20 real requests").
- [ ] Decide the interpreters (proposed default: gated on CPython 3.13 and 3.14. 3.11 and 3.14t are informational, so
  free-threading has numbers even though D8 has no performance gate). Linux = x86_64 Linux on the A-05 reference
  host, with uvloop. macOS = arm64. Windows is not gated. Record and flag.
- [ ] Absolute µs and bytes are reported next to every ratio; there is no absolute threshold.
- [ ] Fix the spike type list as the closure of the gated fixtures (proposed: Update, Message, User, Chat,
  MessageEntity, PhotoSize, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InaccessibleMessage +
  `MaybeInaccessibleMessage`, the four `MessageOrigin*` + `UnknownMessageOrigin`, LinkPreviewOptions,
  ReplyParameters, method `SendMessage`). Every gated fixture must decode without any opaque field (see B-04).
- [ ] State the semantic gates as named test ids, which B-11 and B-07 implement: one wrapper on concurrent first
  access; no deadlock on re-entry; cycles through Bot/session collectable; teardown on 3.11 and 3.14t; two bots can't
  redirect each other's shortcuts (R02).
- [ ] Owner sign-off recorded in Notes. After sign-off, `gate.toml` changes only through a new owner decision that
  is recorded **before** a re-run.
- [ ] Tests: a pytest that loads `gate.toml` and checks every workload references an A-04 manifest id and every
  gated entry has a threshold (100% of new Python).
- [ ] No changelog or registry entry (not user-visible, PD-03).

## Acceptance criteria

- `benchmarks/b_gate/gate.toml` exists. It lists every workload with input id + sha256 from the A-04 manifest, a
  threshold or `informational = true`, platform and interpreter.
- The binding thresholds equal the README B row word for word in `benchmarks/b_gate/README.md`.
- Every "Decide" item above has a recorded choice and a sign-off line in Notes.
- The pytest on `gate.toml` passes.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Warm access ≤1.2× | No native-getter design meets it (aiogram_rust 1.36–1.55×). Replaced by ≤1.6× plus the e2e dispatch gate | D26, 13 §5 |
| A pre-committed fallback (optimised pydantic + Rust codecs) | A failed gate means a model redesign, not a fallback | D104, R01 |
| Gating against stock 3.x or an unmerged 3.x optimisation | The baseline moves (3.32 cut parsing by 39%); unimplemented baselines are forbidden | 13 §1, codex §10, A-06 |
| tracemalloc as the memory estimator | It misses native Rust allocations | R04 |
| Compiled rejectors in the gate dispatch run | They credit routing gains to the model layer; E measures them | B-12, E-09 |
| An abi3 vs per-version wheel comparison | Declined; per-version wheels are kept regardless | 13 B16, D119 |

## Validation

```bash
uv run pytest tests/test_core/test_gate_spec.py
make lint
```

## Workflow notes

- Inputs: the A-04 manifest (fixture ids, sha256), the A-05 harness layout, the A-06 optimised-3.x tag, and the A-10
  realistic router id.
- Outputs: `gate.toml`, which B-02 reads to choose workloads and B-13 reads to judge, plus the type list for B-04.
- Can run in parallel with B-01 and B-03. It must be signed off before B-02 records baseline numbers.

## Notes
