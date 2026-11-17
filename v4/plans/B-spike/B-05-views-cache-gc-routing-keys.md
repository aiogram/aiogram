# B-05 — Python views, wrapper cache, GC, `routing_keys()`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-04](B-04-spike-type-set.md) |
| Blocks | [B-06](B-06-value-semantics-native-api.md), [B-07](B-07-bound-views.md), [B-08](B-08-subclassing-register.md), [B-09](B-09-sendmessage-encoder-response.md), [B-10](B-10-ext-helpers-stub-workflow.md), [B-11](B-11-cache-gc-teardown-ft-tests.md), [B-12](B-12-dispatch-harness.md), [E-09](../E-runtime/E-09-routing-keys-compiled-rejectors.md), [B-13](B-13-gate-run-and-decision.md), [C-18](../C-butcher/C-18-rust-type-emitter.md), [H-13](../H-testing-observability/H-13-binding-identity-rewrite.md) |
| Gate-conditional | no |
| Decisions | D4, D26, D53, D105, D106, D108 (raw), R03, R04, PD-03 |
| Sources | [01-models.md §3.1, §4](../../research/01-models.md), [07-free-threading.md §2](../../research/07-free-threading.md), [03-routing.md §3 "Routing keys in one call"](../../research/03-routing.md), [08-build-release.md §7 items 2–6](../../research/08-build-release.md), [13-aiogram-rust-review.md B2, B14](../../research/13-aiogram-rust-review.md), [19 D105, D106, R03, R04](../../research/19-review-resolutions.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

First access (≤2×) and warm access (≤1.6×) are decided by the wrapper and its cache. Uncached native getters lose to
pydantic (aiogram_rust 0.65×, 13 §1), and a fixed N-slot cache defeats the memory target (R04). The cache must also be
safe on free-threaded builds without ever blocking while Python runs (R03). `routing_keys()` exists because a Python
router reading native attributes one FFI call at a time is 13% slower than 3.x (13 B14).

## Scope

**In:**
- **Wrapper.** A `#[pyclass(frozen)]` per type with fields: `data: Arc<T>`, `bot: Option<Py<PyAny>>` (the view's
  bot), `raw: Arc<[u8]>` (this update's own bytes, plus the object's byte range) and a **sparse cache**. The cache has
  slots only for non-scalar fields that are present (R04).
- **Publication (R03).** A child wrapper is built outside any lock and published with an atomic compare-and-set; the
  loser is dropped. Re-entrant initialisation is never under a lock. `PyOnceLock` only for process-wide globals.
  `msg.chat is msg.chat` holds within one view.
- **GC (R03).** `__traverse__` / `__clear__` on every wrapper report each owned `Py` (bot, cached children, cached
  strings) **exactly once**.
- **Getters.**
  - Scalars are converted on access.
  - Strings are cached after the first access.
  - Interned Python strings for enum values are created once per process: a pyclass-free global, interpreter-bound;
    subinterpreters are unsupported (PyO3 refuses import).
  - Unix-time fields return UTC `datetime`.
  - Enum fields return `str`, matching today's `use_enum_values`.
- **Collections (D106).** Cached tuples, identity-stable.
- **Raw access (D108 part).** `.raw` returns a fresh `dict` on every access; `.raw_json` returns the received bytes
  slice for wire objects. Constructed-object raw is B-06.
- **Unknown attributes (D105).** On an attribute miss, `__getattr__` looks the name up in the object's unknown keys
  and returns the decoded value with a one-time warning per `(type, name)`. Otherwise `AttributeError`. There is no
  cost on hits.
- **`Update.routing_keys()` (B14).** One call returning a frozen `RoutingKeys`, cached per view, with:
  - `event_type`;
  - command `(prefix, name, mention, args)`, parsed with the **exact** 3.x `CommandObject` rule
    (`aiogram/filters/command.py`, `Command.extract_command`: `text.split(maxsplit=1)`, then the `@` mention split),
    or `None`;
  - `text` (`text` or `caption`, as 3.x `Command` reads it);
  - `callback_data`;
  - `chat_type`;
  - `content_kind`, from a hand-written spike content-kind table over the spike fields. The full Rust table is C-19's (overlay kind 14).
- **Python-facing errors.** The Python class for a per-update decode error (path, message, raw, `update_id`) and
  `Update.decode_error` (10 Layer 2). `from_json` / `from_dict` raise `ValueError`.
- **Module and stubs.** `module = "aiogram.types"` on every class; `freelist` on `User`, `MessageEntity`,
  `PhotoSize`; no `dict` / `weakref` slots (08 §7 item 6). `aiogram/_core.pyi` stubs for the spike classes.
- **Entry points.** `_core.decode_update(raw: bytes, bot=None) -> Update` and
  `_core.decode_updates_response(raw: bytes, bot=None) -> tuple[Update, ...]`.

**Out:**
- Constructors, `to_*` / `from_*`, `replace`, eq / hash, pickle, seeding (B-06).
- `as_()` (B-07). Subclass registry (B-08).
- Compiled rejectors that consume `routing_keys()` (E-09).
- The real `AiogramDeprecationWarning` class and once-filter machinery (I-12 / 3x-20).

## Checklist

- [ ] Wrapper struct, sparse cache (present non-scalar fields only), atomic-set publication.
- [ ] `__traverse__` / `__clear__` reporting each reference once. A unit test counts visits through `gc.get_referents`.
- [ ] Getters for every value kind; cached strings; interned enum strings; tuples for collections; UTC datetimes.
- [ ] `.raw` (fresh dict per access) and `.raw_json` (wire slice).
- [ ] D105 warning from the `__getattr__` miss path, deduplicated per `(type, name)`. The spike uses a local
  `warnings.warn(..., DeprecationWarning)` shim so the gate does not wait on I-12 (which depends on butcher's C-10);
  C-18 replaces the shim with I-12's `warn_once` + `AiogramDeprecationWarning` when wiring types (C-18 checklist).
- [ ] `__getattr__` fallback for unknown keys (D105), with a test that the hit path is unchanged (benchmark the
  attribute read with and without unknown keys present).
- [ ] `RoutingKeys` and `Update.routing_keys()`, with command parsing parity against `Command.extract_command` on a
  matrix of inputs including U+001C–U+001F, NBSP and surrogate pairs (03 §3).
- [ ] Python decode-error class, `Update.decode_error`, and the `decode_update` / `decode_updates_response` entry
  points.
- [ ] `module = "aiogram.types"`, freelists, and `_core.pyi` entries.
- [ ] Register the first-access, warm-access, collection and `routing_keys` workloads in the B-02 adapter.
- [ ] Tests in `tests/test_core/`: identity within a view, tuples, raw freshness (mutating `.raw` changes nothing),
  D105 warning once, routing-key parity, decode-error update (100% of new Python).
- [ ] No changelog or registry entry here (not wired, PD-03). Breaking change 23 (tuples) and the D105 deprecation
  get registry entries from the plans that wire types into `aiogram.types` (C-18, I-17).

## Acceptance criteria

- `update.message.chat is update.message.chat` and `update.message.entities is update.message.entities` hold.
- On cp314t, 16 threads making the first access to `update.message` all receive the identical object (smoke here,
  full suite in B-11).
- `routing_keys()` agrees with 3.x `Command.extract_command` on 100% of the parity matrix.
- The B-02 first / warm access workloads run (numbers are judged in B-13, not here).
- `gc.get_referents(wrapper)` lists each owned reference exactly once.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Eager materialisation of all wrappers at parse | Memory is the target; laziness also gives identity within a view and O(1) re-mount | D4, 13 §4 |
| Uncached native getters | 0.65× pydantic | 13 §1 |
| A fixed `[OnceLock; N]` cache per type | Storage proportional to field count on wide types | R04 |
| Building the child under a lock (`OnceLock::get_or_init`) | Can deadlock when initialisation runs Python | R03 |
| A mutable cached `.raw` dict | Fresh dict on every access | D108 |
| One FFI getattr per handler for routing | 13% slower than 3.x | 13 B14 |
| Unknown fields dropped from attribute access | Kept for one D71 window with a warning | D105 |

## Validation

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: B-04 types; B-02 adapter for workload registration.
- Outputs: the `RoutingKeys` contract for E-09 (fields, caching, split rule); the wrapper and cache model that B-06,
  B-07, B-08 and B-11 build on; the decode entry points used by B-09 and B-12.
- After this, B-06 / B-07, B-08, B-10 and B-11 can run in parallel.

## Notes
