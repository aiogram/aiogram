# 13 — Review of the community port `andrew000/aiogram_rust`

Reviewed 2026-11-17 at commit `7d7902a4`, read-only. It is an independent port of 3.32.0 / Bot API 10.4: about
222k lines of Rust, with eager `#[pyclass]` types, a reqwest + tokio transport and abi3 wheels. There is no PyPy and
no free-threading. Routing, FSM and webhook are the 3.x Python code with a native prefilter added. The owner treats
it as **a source of lessons, not of code** (`dialogue.md`). This doc records what we take, what confirms our
decisions, and where we deliberately differ.

## 1. Their numbers

All numbers are from a warm process on Windows with Python 3.14.10, against 3.32.0 + pydantic 2.14.3
(`bench/RESULTS.md`).

| Stage | Theirs | 3.x | Ratio |
|---|---:|---:|---:|
| `Update` from JSON | 3.55 µs | 25.8 µs | 7.28× |
| small message from JSON | 0.84 µs | 6.47 µs | 7.70× |
| `Update` from dict | 8.40 µs | 28.6 µs | 3.40× |
| `model_dump_json` | 1.21 µs | 15.3 µs | 12.6× |
| `model_dump` | 7.88 µs | 17.3 µs | 2.19× |
| build `sendMessage` request | 3.18 µs | 16.4 µs | 5.17× |
| `msg.text` / `msg.from_user.id` | 48 / 79 ns | 31 / 58 ns | **0.65× / 0.73×** |
| memory per update, import time | not measured | | |

- **The baseline moves.** aiogram 3.32 + pydantic 2.14 alone cut parsing from 41 to 25 µs (−39%), so their ratios
  fell between re-benches. That confirms our rule to gate against an *optimised* 3.x (09) and to also check
  absolute µs.
- **Routing** (µs per update):

  | Case | 3.x | 3.x + inline magic | Theirs, prefilter off | Theirs |
  |---|---:|---:|---:|---:|
  | 1 handler | 20 | – | 12.2 | 12.1 |
  | 20 × `F.text ==` | 1 735 | 55.8 | 48 | 14.9 |
  | 100 Commands | 280 | – | 317 | 18.3 |
  | 5 routers / 30 handlers | 785 | 69 | 52 | 31 |

  Most of their routing win is the `to_thread` fix (09 #1). With the prefilter off, their Python path is **13%
  slower** than 3.x, because every attribute read crosses into Rust.
- **Transport:** reqwest over the tokio↔asyncio bridge is +40–80 µs per sequential request, and equal at 100
  concurrent requests.
- **Build:** cold release build 215 s on 32 cores, 9–11 min per platform in CI, stripped binary 56 MB.

## 2. What confirms our decisions

| Theirs | Ours |
|---|---|
| A fully native dispatch loop was built and **rejected**: about 13 µs per update is Python middlewares + asyncio scheduling (PLAN 16.2) | D5: routing stays Python |
| tokio/reqwest: +40–80 µs per request, a shutdown crash on CPython <3.13.8, about 120 lines of cancellation cleanup with a leak window, and proxy chains, custom SSL, trace configs and fork safety lost (most of that undocumented) | 05: keep aiohttp, no tokio |
| pyo3-stub-gen dropped; stubs are generated from the IR (`gen` went from 12 min to 7.3 s) | 02 §5.1 |
| An unknown union tag is a hard error; an unknown update type raises; extras are eager Python objects | D10 is ahead |
| Their generator reads legacy butcher's output and the upstream `.py` files | D6 is independent of that |
| Uncached getters lose to pydantic (0.65×) | 01 §3.1 caches on access |

## 3. Borrowed (applied in the docs named)

| # | Lesson | Evidence | Where |
|---|---|---|---|
| B1 | **Table-driven decode**: the generator emits a field table + `Partial`/`set_once`/`finish` instead of `#[derive(Deserialize)]`; no `#[serde(flatten)]` (unknown fields / `.raw` are raw slices) | −196k macro lines, −10% warm build, **1.35× faster parse** (`flatten` forces `Content` buffering) | 01 §3.1, 02 §5 |
| B2 | `intern!` every key emitted by `to_dict` (formerly `model_dump`); `as_str`-style getters with no clones | `model_dump` 2.23× | 01 §3.5, 08 §7 |
| B3 | The shared surface (`to_json` / `to_dict` / `from_*` / `replace`, D91; `__eq__`, `__repr__`, pickle) lives **once on the base class**, dispatched through a per-type vtable/capsule. Constructors are `(**kwargs)` → `from_dict` | −24.5% generated source, −41% `cargo check`, binary 68→54 MB | 02 §5, 08 §7 |
| B4 | Release profile: **thin LTO, 16 codegen units**, never fat LTO | fat: 11.9 vs 3.7 min, ran a 16 GB aarch64 runner out of memory; thin is within 2% on speed | 08 §3 |
| B5 | ~~**Crate layout from day one**~~ **superseded by §7 / D102 (one crate)**: generated types in their own crate, frequently edited hand-written code in a crate above it | the types crate is 157 s of a 158 s build; touching hand-written code drops from 12 s to 3 s; a later 620-file move cost +11–13% binary size | 08 §2 |
| B6 | **pyo3 ≥ 0.30, and benchmark in a "warm" state.** Any `Py` dropped while detached arms pyo3's reference-pool mutex on every call, about 7–15 ns | `msg.text` 43→57 ns on 0.29; 0.30 fixed it | 01 §5, 07 §2, 08 §3 |
| B7 | **Depth bound** (128) + `stacker` on decode; iterative dealloc for deep trees on 3.11 | they found a real stack overflow and GC cases | 01 §3.1 |
| B8 | **Differential harnesses with a poison control**: model, request and routing traces compared across two venvs (3.x vs 4.0). A poisoned side must produce mismatches, or the harness counts as broken | 4 real model bugs in 2 800 cases; native and fallback encoders disagreed on 12/300 requests | README milestones D and E (framework A-07), 08 §5 |
| B9 | **Cancellation fuzz** for uploads and downloads (4 boundaries × 8 seeds, 4 leak checks) | caught a leak that reproduced on 8 of 8 seeds | 05, milestone D |
| B10 | **Typing check against the installed wheel** (`assert_type`, run from outside the repo) + stubtest. Hand-written surface must reach the stubs | their stubs were missing 203 members until checked | 02 §5.1, 08 §5 |
| B11 | clippy **restriction lints** `unwrap_used`, `expect_used`, `panic`, `todo`, `unimplemented` = deny; they are not masked by `allow(clippy::all)` in generated files | | 08 §5 |
| B12 | CI: rust-cache with `PYO3_ENVIRONMENT_SIGNATURE` (otherwise a stale libpython path gets replayed), incremental and debuginfo off, path-filtered PR jobs, wheel builds cached too. (Their aarch64 rustls / `manylinux_2_28` note doesn't apply: no Rust networking, R25) | | 08 §5 |
| B13 | **Prefilter, rebuilt in Python** on the compiled routing snapshot (D114), with a sound skip rule (03 §3) | 20 Commands 5.4×, 100 Commands 17× native; one rejection 2.6 µs → 0.06 µs | 03 §3 |
| B14 | **Routing keys in one Rust call per update** (`update.routing_keys()` → command, text, callback data, chat type, content kind) instead of one FFI read per handler | their Python routing over native objects is 13% slower than 3.x | 03 §3, 01 §5 |
| B15 | **Topology epoch** (a global counter bumped on any middleware/router change) to invalidate cached chains on 3.x | single handler 18.6 → 13.4 µs | 09 #11 |
| B16 | ~~Measure abi3 vs per-version wheels in the spike~~ **declined**: per-version wheels are kept regardless, and the CI cost is accepted | | 08 §4 |
| B17 | Encoder details found by their fuzzing/reviews: a `timedelta` is never chrono `[secs, nanos]`; aiogram encodes it as the absolute unix time `now + delta`, as 3.x does, because relative seconds would make a temporary ban permanent (PD-11); naive datetimes are local time; half-even rounding; `from`/`from_user` and `bot`/`bot_user` both accepted on every input path; `timeout <= 0` means no deadline | | 01 §3.1, 05 |

## 4. Where we deliberately differ

| Topic | Theirs | Ours | Why we keep ours |
|---|---|---|---|
| Hand-written helpers | 4 974 lines of Python attached to the native classes at import | **D11 kept**: Rust `*_ext.rs` | One language per type, native speed. Accepted cost: helper changes need Rust and a rebuild of the one core crate (D102 placement rules, §7) |
| Object materialisation | eager: every nested object is a pyclass at parse time | **D4 lazy kept** (01 §3.1) | Memory is the target, and they never measured it. Laziness also gives cached identity (within a view, D103) and O(1) re-mount |
| Bot binding | per object, tree walk on validate (about 0.47 µs per update) | independent bound views (D103, replaces one `Ctx` per tree) | O(1) `as_()` / re-mount as a new view; no shared mutable context |
| Mutability | `MutableTelegramObject` kept | D15: everything is immutable | free-threading |
| Prefilter semantics | skips a handler on any certain reject, even if user filters come first (BREAKING.md "guaranteed-false filters may be skipped"); Rust `split_whitespace` ≠ Python `str.split` for U+001C–U+001F (inferred from the code, not run) | **same skip rule, adopted** (03 §3, README breaking change 13); command parsing reuses the exact Python splitting rule | faster; documented as a break |
| Wheels | abi3, CPython only | per-version + ft + PyPy (D7, D8); B16 declined | abi3 can't load on free-threaded builds |
| Requests | always multipart | JSON body unless files are attached (05 §2) | smaller, faster |
| i18n | absorbed `aiogram_i18n`, renamed 3.x middleware classes | **D25: absorbed too, 3.x names kept** (06 §3) | no rename churn |

## 5. Gate change

Warm attribute access was gated at ≤1.2× pydantic. No measured native-getter design meets it (theirs: 1.36–1.55×
slower). The gate becomes **≤1.6× on raw access**, plus an **end-to-end dispatch gate**: with B14, a realistic
router must be no slower than optimised 3.x. See the README roadmap and 01 §5.

## 6. Their breaking-change entries we must decide on explicitly

Decided in 01 §3.6 (D83–D87); the items below are listed under README breaking changes 3, 18 and 19:
- Multiple inheritance is flattened by PyO3's single inheritance. `isinstance(x, SecondaryBase)` becomes False
  unless the generator emits `register`-style ABC checks.
- Equality between a subclass and its base.
- How ambiguous undiscriminated unions are resolved (tag or overlay predicate, otherwise `Unknown`; declaration order dropped by D107).
- `by_alias` and wire names in `model_dump_json`.
- Extras must be JSON-shaped.
- Depth bound of 128.

## 7. PR #11 "place generics with their class" (merged 2026-11-17)

One crate, 32 cores, Windows: cold release build 214 → 78 s, dev 57 → 44 s, binary 56.4 → 47.5 MB,
LLVM IR 8.0 → 6.8 M lines; per-update `getUpdates` batch 6.2 → 3.8 µs; `sendMessage` response 3.0 → 2.0 µs; every
other benchmark 0.94–1.03×. **Finding:** the build wasn't slow because of how much code there was. It was slow
because the code sat in two codegen units: one core was busy for about 190 s, and the units were 135 / 80 MB against
6–14 MB for the rest.

| # | Lesson | Where |
|---|---|---|
| B18 | rustc (current partitioning heuristic, verified by B25, R25) places a generic instance in the unit of the **defining module**, so per-class shared code must be trait methods with `Self` = the class, `#[inline(never)]` bodies, `#[inline]` one-line delegations | 08 §7 item 13 |
| B19 | Stack guard by **re-entry** (body compiled once) plus a single `dyn` `stacker::grow` instance | 08 §7 item 14, 01 §3.1 |
| B20 | Generated code binds field values to locals: `Self { a: x(a)?, … }` produces cleanup that grows with the square of the field count | 02 §5 |
| B21 | Hoist class-independent code out of per-class functions | 02 §5, 08 §7 item 15 |
| B22 | Parse the response envelope by borrowing `result` as raw text; no intermediate tree. (They use serde_json `raw_value`; we use jiter `current_index` / `known_skip` / `slice_to_current`, verified on 0.19.0) | 05 §2.2, 10 §3 |
| B23 | Unions decode the chosen variant from the raw slice; they still buffer a tree here (about 10% of their IR plus a second pass) | 01 §3.1, D85 |
| B24 | Benchmark the bot's real path (batch + response); their headline 7.3× was 4.0× on the polling path | 01 §5, README milestone B |
| B25 | CI watches the **largest codegen unit** and the phase split (`-Ztime-passes` on a separate nightly job, threshold calibrated on CI hardware, R25), not total code (total IR −15% bought almost nothing) | 08 §5 |

Tried and dropped there (08 §7 item 16): `#[inline]` on widely used generic wrappers (+7–8% build); `lto = "off"`
(build −35%, JSON dump +58%); `codegen-units` 8–256 (no effect); `dyn` on hot-path closures (parse 5–9% slower);
out-of-line `dyn` stack helper (+17 s). Caveat: the gains are idle cores put to work on 32 cores, and a 4-core CI
runner will gain less (not measured). → **D102: one crate.**
