# 07 — Free-threaded Python (no GIL)

Target (D8): **CPython 3.14t and 3.15t**, first-class, tested in CI. 3.13t is out of scope: PyO3 0.29 dropped
it and pydantic-core no longer ships `cp313t` wheels.

## 1. Execution model we support

One process, N threads, **one asyncio loop per thread** (per-thread loops are supported; asyncio objects
themselves are **not** thread-safe, R12). Shared between threads: the `Dispatcher` (each Runner routes on its own
immutable snapshot, D114), routers, filters,
storages, isolation. Per thread/loop: `Runner`, `Bot` + aiohttp session (loop-bound), Redis clients (loop-bound).
Loop-bound objects (`asyncio.Lock`, futures, tasks) are never shared. Cross-thread hand-off uses
`call_soon_threadsafe` / `run_coroutine_threadsafe`.

A helper is planned: `dp.run_polling_threads(bot_factory, threads=N)`. It runs one `Runner` per thread
([12](12-runtime.md)) with bots sharded across them. For a single high-traffic bot there is **one ingress poller**
per bot (one `getUpdates` offset), which hands updates off to the worker Runners sharded by the **isolation key**
(R12), preserving per-key ordering. Only the main-thread Runner owns signals. Design detail to be done in phase 4.

## 2. Rules for the Rust core

- Module declares free-threading support (PyO3 ≥0.28 default; never `gil_used = true`).
- Every `#[pyclass]` is `Send + Sync`, `frozen`. No `&mut self` methods anywhere; mutable state goes in
  `Mutex` (`lock_py_attached`) or atomics. Wrapper caches build outside any lock and publish with an atomic
  `set` (R03, 01 §3.1); `PyOnceLock` only for process-wide globals. Use `with_critical_section` when touching
  a Python container we don't own.
- Never hold a Rust lock while calling into Python (deadlock).
- Wrap Rust-only work ≥1 ms (large `getUpdates` decode) in `py.detach(...)` so other threads, and on GIL
  builds other Python code, keep running.
- Handed-out Python containers are fresh copies or tuples (01 §4).

## 3. Python-side work (from 03 / 04)

| Component | Change |
|---|---|
| Dispatcher | per-Runner routing snapshot (D114), per-loop `Runner`; changes after start apply on restart or `runner.refresh()`, with a one-time warning |
| `SimpleEventIsolation` | lock table that works across threads and loops, with pruning (04 §3) |
| `MemoryStorage` | sharded locks, atomic `update_data`, history copy-on-write |
| Scenes/StatesGroup registries | captured in the Runner's snapshot (D114); later changes apply on refresh |
| `Bot._me` / `_usernames` caches | idempotent races, acceptable; use `PyOnceLock`-like `threading.Lock` init if needed |
| Mongo | `PyMongoStorage` only; motor-based `MongoStorage` removed |
| pydantic | not a dependency (D14), so a free-threaded install doesn't pull pydantic-core |

## 4. Dependency readiness (PyPI, 2026-11)

| Status | Packages |
|---|---|
| ft wheels for 314t + 315t | pydantic-core (only for the optional interop hooks, D14), aiohttp, multidict, yarl, propcache, uvloop, pycares, hiredis, pymongo |
| 314t only | cryptography |
| 313t + 314t, **no 315t** | frozenlist 1.8.0 (an aiohttp dependency): watch it |
| pure Python | fluent.runtime 0.4.0 + fluent.syntax, fluent-compiler 1.1, babel, attrs, pytz (i18n extras, D25; fluent.runtime last released 2023-03), opentelemetry-api/sdk 1.45.2 (otel extra, D64), aiohappyeyeballs, aiodns, redis, magic-filter, certifi |
| **no ft wheels** | orjson (never require it; docs must not recommend it for ft builds), motor (replaced) |

Tracker: https://py-free-threading.github.io/tracking/

## 5. CI

- Jobs on `3.14t` and `3.15t` (Linux + macOS) running the full suite with `PYTHON_GIL=0`, and failing if the
  GIL gets re-enabled at import (`sys._is_gil_enabled()` check in conftest).
- Race regression tests from 04 §2, plus: concurrent decode of one shared `Update` object from N threads,
  `as_()` views of one payload for different bots under contention (D103: neither redirects the other),
  lazy-attribute first access from N threads (must return the identical object within one view).
- Optional: a ThreadSanitizer job for the Rust core (`RUSTFLAGS=-Zsanitizer=thread`, nightly) on a schedule.
