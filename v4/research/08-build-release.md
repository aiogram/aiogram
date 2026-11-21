# 08 — Build, release, contributor workflow, Rust↔Python best practices

## 1. What pydantic does (reference model)

- `core_schema` dicts are the contract between Python and Rust. `SchemaValidator`/`SchemaSerializer` compile them
  into a Rust validator tree. Python extensibility comes from validator/serializer schemas holding Python callables,
  plus `__get_pydantic_core_schema__`.
- pydantic-core was **merged back into the pydantic monorepo** (v2.13, PR pydantic/pydantic#12481). It is still
  published as a separate distribution, **exact-pinned** (`pydantic-core==X.Y.Z`; mismatch raises at import
  since 2.12).
- Build: maturin, `python-source = "python"`, module `pydantic_core._pydantic_core`, PyO3 0.30, jiter for JSON.
- Wheels: 140 files per release, **no abi3**. cp310–cp315 + cp314t/cp315t, manylinux (x86_64, i686, aarch64,
  armv7l, ppc64le, s390x, riscv64), musllinux (x86_64, aarch64, armv7l), macOS x86_64/arm64, Windows
  x86/x64/arm64, PyPy 3.11, GraalPy, emscripten. **No pure-Python fallback.** (Precedent only: we do not ship PyPy wheels, PD-35.)
- Their own guidance: Python callbacks inside Rust (wrap validators) are slow, and `model_validate_json` beats
  `json.loads` + `model_validate`. In short: **cross the boundary rarely, with big payloads.**

What we copy: maturin + PyO3 + jiter/serde, mandatory core, per-version wheels, a monorepo, generated code.
What we don't copy: the schema-interpreter design. We **generate** concrete Rust structs instead of interpreting
a schema at runtime, because Telegram types are fixed per release and we own the generator.

## 2. Repository layout (single distribution, D17)

```
pyproject.toml          # build-backend = "maturin"; [tool.maturin] python-source = ".", module-name = "aiogram._core"
Cargo.toml              # workspace (crate + butcher + xtask)
crates/aiogram-core/    # ONE crate: generated/ + hand-written decode/encode/entities/ctx + *_ext.rs, PyO3 bindings
aiogram/                # Python package (unchanged location)
aiogram/_core.pyi       # hand-written stub for the non-generated surface, checked by stubtest (PD-36); generated stubs live beside types
crates/butcher/         # generator, run via `cargo xtask butcher` (02 §5)
butcher/                # overlay, ledger, IR snapshots (02)
```

**One crate, with codegen-unit-aware placement (D102, revises the 3-crate plan from 13 B5).** aiogram_rust PR #11 got
−137 s of release build and −16% binary inside a single crate, while their crate split gave −57 s for +11% binary.
The slowness came from code that **landed** in two codegen units, not from how much code there was. The rules in
§7 (items 13–16) apply from day one, and CI guards the largest unit (§5). Generated structs carry `#[pyclass]`
directly; the Python-visible wrapper model (data + bound view + cache) is defined in 01 §3.1 and is normative over
this page (19 §8). `*_ext.rs` sit next to their types (D11). **Spike fallback:** if
edit-rebuild time for hand-written glue hurts contributors, the spike also measures a glue crate above the types.
`cargo test` still covers decode/encode/entities without Python where possible (`#[cfg(test)]` on pure functions).

Why a single distribution (vs an `aiogram-core` split): Bot API bumps change Rust and Python in lockstep, and a
split adds an exact pin, two release pipelines and a version-mismatch failure mode for no benefit. The pure-Python
code still ships inside each wheel. Revisit only if Python-only patch releases become frequent enough that
rebuilding the wheel matrix hurts.

## 3. Toolchain & versions

| Item | Choice |
|---|---|
| PyO3 | **≥0.30** (Bound API; `attach`/`detach` naming; MSRV Rust 1.85). Older versions lock the reference-pool mutex on every call once a `Py` was dropped detached (13 B6) |
| Release profile | `opt-level = 3`, **`lto = "thin"`, `codegen-units = 16`**, `strip = true`. Fat LTO tripled build time and ran a 16 GB runner out of memory for ≈2% (13 B4). Expect ≈50–60 MB stripped binary, 9–11 min per platform in CI |
| Rust MSRV policy | latest stable − 2 minors; pinned in `rust-toolchain.toml` for CI reproducibility |
| JSON | `jiter` (decode, used by pydantic) + `serde`/`serde_json` or hand-written writer for encode |
| Concurrency prims | `arc-swap`, `std::sync::OnceLock`, `parking_lot` only if profiling asks for it |
| Build backend | maturin ≥1.14 (needed for future `abi3t`) |
| Async | **none in Rust**: no pyo3-async-runtimes, no tokio, no `experimental-async` |

## 4. Wheel matrix

**Release-blocking tiers (D119).** **Tier 1** (blocks a release): CPython cp311–cp315 + cp314t/cp315t on manylinux
x86_64/aarch64, musllinux x86_64/aarch64, macOS arm64/x86_64, Windows x64. **Best-effort** (never blocks):
Windows arm64, i686/armv7l/ppc64le/s390x. PyPy is not supported (PD-35). An sdist is always published.

- CPython **cp311–cp315**, per-version (abi3 can't load on free-threaded builds, and per-version keeps the
  version-specific speedups). Kept regardless of an abi3 comparison: the CI cost (≈10 min per wheel) is
  accepted (13 B16 declined).
- Free-threaded **cp314t, cp315t**.
- Linux manylinux x86_64/aarch64 (+ best-effort i686, armv7l, ppc64le, s390x); musllinux
  x86_64/aarch64; macOS x86_64/arm64; Windows x64 (+ best-effort arm64; x86 if users ask).
- No PyPy wheels: PyPy is not supported in 4.x (PD-35, supersedes D7); stay on 3.x.
- Later (a separate decision from B16, which only declined an abi3 comparison for 4.0): when the floor reaches 3.15, switch the non-ft wheels to `abi3` and ft wheels to `abi3t` (PEP 803,
  Final), which collapses the matrix.
- sdist published, but building it needs Rust ≥ MSRV (documented; affects exotic platforms and Termux).

≈60–90 wheels per release. Built with `maturin-action` (`maturin generate-ci github` as the starting point);
cibuildwheel is the alternative if we need its test-in-wheel matrix.

## 5. CI

- PR: `cargo fmt --check`, `cargo clippy -D warnings`, `cargo test`; Python lint/mypy/pytest on a single
  wheel built with `maturin develop --release`; butcher `check` (committed output == regenerated); `stubtest`.
- Matrix: 3.11–3.15, 3.14t/3.15t, Windows, macOS; no PyPy (PD-35).
- clippy restriction lints `unwrap_used`, `expect_used`, `panic`, `todo`, `unimplemented` = deny, also in generated
  code; `allow(clippy::all)` there doesn't mask them (13 B11).
- **Largest-unit guard (B25):** a scheduled release build with `-C save-temps` records the per-unit object sizes. It
  fails if the largest unit exceeds 2× the median or the cold build regresses by more than 15%, because the total
  amount of code is not the signal. The threshold is calibrated on real CI hardware (R25). The `-Ztime-passes`
  split runs on a **separate nightly-toolchain job**, so the compiler being compared never changes.
- Typing: `assert_type` checks against the **installed wheel**, run from outside the repo, plus `stubtest` (13 B10).
- Differential harnesses (13 B8), with each side in its own venv and a canonical JSON trace:
  - model decode/dump, 3.x vs 4.0;
  - request encoding, Rust vs the Python fallback encoder;
  - routing outcomes, 3.x vs 4.0.

  Each harness has a poison control that must report mismatches. Plus a cancellation fuzz for uploads and
  downloads (B9).
- Caching (13 B12): rust-cache with `PYO3_ENVIRONMENT_SIGNATURE` in the key; incremental builds and debuginfo off
  in CI; PR jobs path-filtered (Python-only PRs reuse a cached wheel); wheel builds cached too.
- Coverage: Python stays at **100%** (repo rule). Rust coverage via `cargo-llvm-cov` over both `cargo test` and
  the pytest run (instrumented build), with generated code excluded from the threshold.
- Benchmarks: `pytest-codspeed` or `asv` on the spike's benchmark set (01 §5) to catch regressions on PRs.
- Release: trusted publishing (`pypa/gh-action-pypi-publish` or `uv publish --trusted-publishing always`),
  build attestations; zizmor already gates workflows (`make lint-workflows`).

## 6. Contributor workflow

- `rustup` required. `uv sync` builds the extension through maturin. Set `[tool.uv] cache-keys` to include
  `Cargo.toml`, `Cargo.lock` and `crates/**/*.rs` so edits trigger rebuilds.
- `make dev` = `maturin develop` (debug) for fast iteration; `make bench` builds release.
- Most contributions (dispatcher, FSM, filters, docs, session) stay pure Python, so contributors never touch Rust
  unless they change the data plane. Bot API bumps are butcher-only.
- Debugging across the boundary: `py-spy record --native`, `perf` with `-X perf`. Rust panics surface as
  `PanicException`; map our errors to Python exceptions explicitly with `create_exception!` + `From<…> for PyErr`.

## 7. PyO3 best practices we adopt (checklist)

1. Coarse calls: one `decode(bytes)` / `encode(method)` per request, never per field.
2. Keep `Bound<'py, T>` on hot paths, store `Py<T>` only in structs, avoid clones.
3. `intern!` for attribute names and dict keys; pre-intern enum strings once.
4. `cast` over `extract` chains on hot paths (error construction is costly).
5. Pass Rust tuples as call args (vectorcall).
6. `#[pyclass(frozen)]` + `Py::get()`; `freelist = N` for small high-churn types (`MessageEntity`, `PhotoSize`,
   `User`); `weakref` only where users need it; no `dict` (unknown data lives in `.raw`, D10).
7. `py.detach` around Rust-only work ≥1 ms.
8. Exceptions: our own hierarchy, never leak a `PanicException` for bad input (`ValidationError` instead).
9. Typed stubs generated and stub-tested; `py.typed` shipped.
10. Measure before porting: every Rust addition needs a benchmark in the suite showing the win.
11. Shared surface once on the base class through a per-type vtable; generated per-type code is data (field
    tables), not methods. Constructors take `(**kwargs)` → `from_dict` (13 B3).
    The generated `text_signature` uses `...` for nonliteral defaults (`inspect` rejects `Default('parse_mode')` in
    a text signature); the stubs carry the real defaults (19 §8).
12. Before optimising compile time, run `cargo llvm-lines`: in aiogram_rust the cost was large per-type field
    walks (`Message::field_values` was 44k IR lines), not generics. Toolchain levers (cranelift, `-Zthreads`, lld)
    measured ≈0.
13. **Generic placement (13 B18):** with the current rustc partitioning heuristic (not a language guarantee; verified
    by the B25 guard, R25), an instantiated generic lands in the codegen unit of the module that *defines* it. Per-class shared code (vtable shims, decode visitor, `to_json` / `from_json`, validation) is written as
    trait methods whose `Self` is the class, so each instance lands in that class's module. Never write
    `fn f<T>` or `impl<T> Tr for Wrapper<T>` for per-class work. Per-class bodies are `#[inline(never)]`, and the
    one-line delegations to them are `#[inline]`.
14. **Stack guard by re-entry (B19):** `if stack_low() { return on_fresh_stack(|| Self::same(args)) }`, with the body
    written once; `stacker::grow` is reached through one `dyn` function. Never `grow(|| body)`, which compiles every
    body twice.
15. **Hoist class-independent code** (unknown-key buffering, hashing, envelope parsing) out of per-class functions (B21).
16. **Don't** put `#[inline]` on generic wrappers with many callers, or `dyn` on hot-path closures, and don't drop LTO
    (`lto = "off"`: build −35% but JSON dump +58%). `codegen-units` beyond 16 changes nothing (aiogram_rust Phase 31).

## 8. Dependencies and extras (D67–D70)

| # | Decision |
|---|---|
| **D67** | **`aiofiles` is dropped.** Path uploads (`FSInputFile`) and downloads to a path use chunked reads/writes in `asyncio.to_thread`, the same thread-pool approach aiofiles uses internally. No API change |
| **D68** | **`docs` becomes a PEP 735 dependency group** (next to `dev` / `test`), so it is no longer a user-facing extra. The `cli` extra goes too: replaced by the built-in CLI ([17](17-cli.md)) |
| **D69** | **i18n extras**: `aiogram[i18n]` = Babel / gettext (name unchanged); `aiogram[fluent-runtime]` and `aiogram[fluent-compiler]` for the two Fluent engines (D25) |
| **D70** | **Lower bounds only.** An upper cap is added only for a major release that is known to break us, with a comment naming the issue. CI runs a scheduled job against the newest releases (`uv lock --upgrade` + full suite), and a minimum-versions job (`uv sync --resolution lowest-direct`) on PRs. A failure in the newest-releases job opens an issue rather than blocking PRs |

4.0 dependency set:

| Kind | Packages |
|---|---|
| core | `aiohttp`, `magic-filter` (D37), `certifi`, `typing-extensions` (while the floor is 3.11) |
| extras | `fast` (uvloop, aiodns), `redis` (`redis[hiredis]`), `mongo` (pymongo only, 11 §5), `proxy` (aiohttp-socks), `signature` (cryptography), `i18n`, `fluent-runtime`, `fluent-compiler`, `otel` (D64), `test` (pytest, D51), `migrate` (libcst, D74), `reload` (watchfiles, D78) |
| removed | `pydantic` (D14), `aiofiles` (D67), `motor` (11 §5), extras `docs` and `cli` (D68) |
| groups | `dev`, `test`, `docs` |

No `all` meta-extra. The Rust core adds no runtime dependencies.
