# aiogram 4.0 — Rust core: research & plan

Status: planned; see [`v4/plans/`](../plans/README.md) (2026-11-18).
Measurements: CPython 3.13.7, macOS arm64, pydantic 2.14.2 / pydantic-core 2.50.2, aiohttp 3.14.5,
best-of-N `timeit`. Numbers marked *est.* are estimates, everything else was measured on `dev-3.x`.

## Decisions taken

| # | Decision | Choice |
|---|---|---|
| D1 | Packaging | **Mandatory Rust core**, pydantic way — no pure-Python fallback |
| D2 | Release target | **aiogram 4.0** — a substantial, documented migration (see Breaking changes), migration guide + tooling required |
| D3 | Priorities | Throughput, memory, startup — weighted by measured impact |
| D4 | Model layer | **Rust-native types** generated from the resolved butcher IR (HTML + OpenAPI adapters); pydantic interop hooks. **Conditional on the spike gate (D104)** |
| D5 | Rust scope | **Data plane only**: models, JSON decode/encode, entity rendering. Routing / FSM / session stay Python (redesigned) |
| D6 | Butcher | Legacy Python butcher retired; **butcher rewritten in Rust** (`cargo xtask butcher`) with **two input adapters (HTML docs + OpenAPI 3.2 schema) → one IR**, cross-checked each release. Compat ledger **reset at 4.0**, then a rolling deprecation window: removed items are kept until the later of **12 months** and **2 Bot API major versions** (`keep_position` dropped by D100: keyword-only signatures) |
| D7 | PyPy | Best-effort `pp311` + `pp312` wheels (PyPy 8.0.1 supports both), tested in CI, no performance promise |
| D8 | Free-threading | First-class on **3.14t+** (see [07](07-free-threading.md)) |
| D9 | 3.x | Separate **quick-wins track** shipped now as bugfix PRs ([09](09-3x-quick-wins.md)) |
| D10 | Forward compatibility | Unknown union tags / enum values / update types decode to `Unknown…` variants; per-update isolation; `.raw` / `.raw_json` on every object ([10](10-forward-compatibility.md)) |
| D11 | Hand-written type helpers | **Rust `*_ext.rs` impl blocks** + `.pyi` fragments merged into generated stubs; `send_copy`, `event_type` generated (`content_type` removed, D12–D15 / 11 §1); no Python facade per type; `InputFile` family stays plain Python ([02](02-butcher.md) §5.1). Conditional on the spike gate (D104, 19) |
| D12–D15, D42 | Legacy removals | class-based handlers (`aiogram.handlers`) removed; `event_from_user`/`event_chat`/`event_thread_id` injection removed (use `event_context`); `utils.markdown` removed; `CallbackData` no longer pydantic, so **pydantic is no longer a dependency**; all types immutable ([11](11-removals.md)). D14 conditional on the spike gate (D104, 19) |
| D16 | Python module layout | **3.x layout kept**: one module + `.pyi` per type/method as thin re-exports; `__init__` imports straight from `_core`; classes report `module="aiogram.types"`; docs show the short import first. Single merged module rejected ([02](02-butcher.md) §5.2) |
| D17 | Distribution (O1) | **Single `aiogram` distribution** built by maturin, Rust core inside; no `aiogram-core` split ([08](08-build-release.md) §2) |
| D18 | Schema-only `Input*` twins (O4) | The 7 `Input*` schemas with no Bot API docs counterpart (`InputBotCommand`, `InputMessageEntity`, `InputChatPermissions`, …) are **merged** into the documented type. The 67 documented `Input*` types are generated as they are ([02](02-butcher.md) §3) |
| D19 | Late registration (O5) | **Per-Runner routing snapshots (D114)**: each Runner compiles an immutable snapshot at start; registering routers/handlers/middlewares later applies on restart or `runner.refresh()`, with a one-time warning; **nothing raises**. D114 replaced the original "raise `RuntimeError` while running" ([03](03-routing.md) §3) |
| D20 | Python floor (O6) | **4.0 keeps `>=3.11`** (PyPy 3.11 + 3.12; re-confirmed 2026-11-17 after checking that PyPy 3.12 exists); a 4.x minor drops 3.11 after its EOL (Oct 2027) |
| D21–D24 | Runtime | Polling/webhook leave `Dispatcher`. **One `Runner` per loop** owns lifecycle and the bot registry; `Poller`, webhook handlers, ASGI app and user sources plug in. Bots are **added/removed at runtime** (no move semantics). No Rust web server. The 3.x webhook bot lookup is kept. `dp.start_polling`/`run_polling`/`feed_webhook_update` stay as wrappers ([12](12-runtime.md)) (D22 wording revised by R13, 19 §2: removal confirms admitted updates, best-effort delivery) |
| D25 | i18n | **Absorbed into core**: gettext and Fluent engines, `I18nContext`, locale managers, lazy text (`L`, `LazyProxy`) on display fields rendered at encode, and `LazyFilter`. 3.x `aiogram.utils.i18n` names are kept; `aiogram_i18n` becomes a migration target ([06](06-utils.md) §3) |
| D26 | Spike gate (attribute access) | Warm raw access **≤1.6×** pydantic (was ≤1.2×), plus an end-to-end dispatch gate. Routing reads its keys in one Rust call per update ([13](13-aiogram-rust-review.md) §5) |
| D27–D30 | FSM | State loading **stays eager**; **isolation on by default** (thread-safe in-process lock table); Redis gets **two storages**, `RedisStorage` (3.x layout, no migration) and `RedisHashStorage` (1 RTT), plus a migration method/CLI and opt-in dual read; **typed FSM data** (`FSMData`, nested types, pluggable pydantic/attrs/msgspec adapters); atomic `update_data` in all built-in storages ([04](04-fsm.md) §4, §6, §7) (D29 revised by D113, 19: `RedisHashStorage` and its migration deferred to 4.x) |
| D31 | DI | Kwargs DI unchanged; typed `ctx: Context` **rejected**. Typed DI is documented via `**kw: Unpack[TypedDict]` (PEP 692) with a documented base `TypedDict` of the built-in keys ([03](03-routing.md) §5) |
| D32 | Dependencies | Public `ParamResolver` hook (`Annotated[T, marker]`, resolved per call, zero cost without markers) + minimal built-in `Depends`: sub-deps, per-update cache, generator teardown **inside the isolation scope** (after `errors` handlers, before the FSM isolation lock is released, PD-04), providers always see the exception (D112), test overrides; usable in handlers, filters, flags, error handlers and middlewares (`await resolve(...)`). Ships in 4.0 and blocks GA (PD-01) ([03](03-routing.md) §5) |
| D33 | Scenes | 3.x semantics kept: shared FSM data, actions picked by update type (now a `RuntimeWarning` when none matches), actions bypass target-scene middlewares (documented), full history snapshots (now one batched storage op). StateFilter compiled into a state index for O(1) scene routing ([04](04-fsm.md) §8) |
| D34–D37 | Filters | Sync filters **inline by default** (`Dispatcher(sync_filters=SyncFilterMode.INLINE \| THREAD)`, a `StrEnum`, per-filter `inline(fn)` / `blocking(fn)`; sync handlers keep the thread); no `&`/`\|` on `Filter`; `RuntimeWarning` when a dict result overwrites existing data; magic-filter stays external, `F` compiled to closures at snapshot compile (D114) ([03](03-routing.md) §5) |
| D38–D41 | Middlewares | `SkipHandler` data sharing kept as in 3.x (documented); registration order + `before=`/`after=` anchors; per-handler `middlewares=[...]` (innermost); generic `BaseMiddleware[EventT, DataT]` for typing ([03](03-routing.md) §5) |
| D43–D46 | Bot client | Opt-in `RetryMiddleware` (429 always, network/5xx only for methods marked `idempotent` in the IR, R19) and opt-in `RateLimitMiddleware` (per-loop token buckets); sessions stay per bot; downloads get per-phase timeouts, `bot.stream()` and typed overloads ([05](05-network.md) §2.5) |
| D47–D50 | Errors | `ErrorReason` enum on `e.reason` (no new exception classes); error handlers **bubble** from the raising router up to the dispatcher; `ErrorEvent` gains `bot`, `router`, `handler`, `phase`; new `dp.runtime_errors` for errors outside update handling ([03](03-routing.md) §5) |
| D51–D54 | Testing toolkit | `aiogram.test` (PR #1887, shipped in 3.33.0) in core, with a pytest plugin **auto-loaded** through a lazy entry-point shim, as in 3.x (D51 revised by the owner, 2026-11-19; not a break); typed call interception; identity via wrapper-cache seeding; official dispatcher **trace hook** (`dp.tracers`) shared with OpenTelemetry/logging ([14](14-testing.md), [03](03-routing.md) §5) (D53 scope revised by D103: identity within one view; mechanism conditional on the gate, D104, 19) |
| D55–D58 | Router API, flags | Observers generated from the IR (typed); no router-level filter; **multiple parents** allowed (cycle check kept, diamonds within one dispatcher raise); `Router(flags=...)` inherited; optional typed flag specs (`@flag_spec`) ([03](03-routing.md) §5) |
| D59–D62 | Utils | D59 ~~opt-in album aggregation `MediaGroupMiddleware`~~ **withdrawn** (D116: deferred out of 4.0); D60 bot commands from `Command(description=...)` + `dp.set_my_commands(bot)`; D61 lazy i18n inside `Text` trees; D62 formatting nodes are the primary style, html/md decorations kept. Builder/media-group/chat-action/`as_*_kwargs` signatures are generated from the IR (a default, not numbered) ([06](06-utils.md) §4) |
| D63–D66 | Observability | Trace hook as **sync span context managers** (revises D54); opt-in `aiogram[otel]` traces + metrics; structured log `extra` + consistent logger hierarchy; **token redaction on by default** (logs, exceptions, webhook access log) ([15](15-observability.md)) (scope revised by R22, 19: filter on every `aiogram.*` logger, `setup_application` access-log limitation) |
| D67–D70 | Dependencies | Core = aiohttp, magic-filter, certifi, typing-extensions; **aiofiles dropped** (to_thread IO); `docs` extra → dependency group, `cli` extra dropped (built-in CLI, D75); extras `fast`, `redis`, `mongo`, `proxy`, `signature`, `i18n`, `fluent-runtime`, `fluent-compiler`, `otel`, `test`, `migrate`, `reload`; **lower bounds only** + CI on newest and lowest ([08](08-build-release.md) §8) |
| D71–D74 | Deprecations & 3.x | aiogram APIs use the ledger window (later of 12 months / 2 minors); `AiogramDeprecationWarning` shown once by default; **3.x: 12 months full support + 6 months security** after 4.0 GA; a named migration-baseline 3.x release warns about every 4.0 removal (R28); `python -m aiogram.migrate fix` (codemod) and `check` ([16](16-support-policy.md)) |
| D75–D78 | CLI | Built-in `aiogram` CLI on stdlib argparse (always installed); `run polling/webhook`, `migrate fix/check`, `info`, `bot me/webhook/commands sync`; plugins via `aiogram.cli` entry points (legacy `aiogram_cli.plugins` loaded with deprecation; aiogram-cli package deprecated); `--reload` via `aiogram[reload]` (watchfiles) ([17](17-cli.md)) |
| D79–D82 | Docs & migration | API reference via sphinx-autoapi on generated `.pyi` stubs (`autoapi_file_patterns = ['*.pyi', '*.py']`, no extension needed at build, R29); Diátaxis-style restructure; Ukrainian translation for narrative docs only; migration guide = impact checklist + per-area pages sharing one registry with deprecation warnings and `aiogram migrate check` ([18](18-docs-migration.md)) |
| D83–D87 | Model semantics | Secondary bases via ABC `register`; equality = same class + data, ignoring the bot binding, and hashable only if all fields are (D108); undiscriminated unions by tag or overlay predicate → `Unknown` (no declaration-order fallback, D107); `model_dump_json()` always wire names; extras JSON-shaped only; depth > 128 = decode error ([01](01-models.md) §3.6). Conditional on the gate (D104) |
| D88–D90 | Testing & routing follow-ups | Own suite: MockedBot for unit tests + toolkit for integration; OpenSpec files dropped from PR #1887; diamonds inside one dispatcher raise (confirms D56) ([14](14-testing.md), [03](03-routing.md)) |
| D91–D95 | Serialization API | pydantic-shaped `model_*` replaced by native wire-centric methods: `to_json`, `to_dict` (wire shape only), `from_json`/`from_dict` (`bot=`), `replace` + `copy.replace`; no public field introspection (`model_fields` removed, D95); other `model_*` kept as deprecated aliases, `model_dump_json` = `to_json` returning `str` ([01](01-models.md) §3.7) (D92 refined by D109: overlay rename rule, exact reserved names, 19; conditional on the gate, D104) |
| D96–D99 | Unreleased API | Raw `bot.call(name, params, returns=None)` only (user `TelegramMethod` subclasses dropped); params may hold `InputFile`/aiogram types/dicts/`to_dict()` objects; optional `returns` (type, builtin, `from_dict` class, callable; default raw JSON); unknown kwargs on generated methods forwarded with a one-time warning ([01](01-models.md) §3.3) |
| D100–D101 | Keyword-only API | **Every generated signature is keyword-only**: type and method constructors (already), `Bot` methods and all shortcuts (`message.answer(text="hi")`, `bot.send_message(chat_id=…, text=…)`); `keep_position` removed from the ledger. Migration: codemod rewrites positional calls, checker reports the rest ([01](01-models.md) §3.4, [16](16-support-policy.md)) |
| D102 | Crate layout | **One crate** with codegen-unit-aware placement rules (generic bodies as `Self`-is-class trait methods, re-entry stack guard, linear field walks, hoisting) and a CI guard on the largest unit; replaces the 3-crate plan (aiogram_rust PR #11: −137 s, −16% binary in one crate) ([08](08-build-release.md) §2, §7; [13](13-aiogram-rust-review.md) §7). Conditional on the spike gate (D104, 19) |
| D103–D121 | Review resolutions | Independent bound views (`as_()` returns a new view); no pre-committed spike fallback, D4-dependent decisions conditional; unknown fields as attributes deprecated; collections = tuples; nearest decoded union absorbs malformed data; raw/hash/equality semantics; overlay rename rule (`bot_user`); isolation escape hatch; flatten-everything routing (break); providers always see the exception, teardown inside the isolation scope (D112, PD-04); RedisHashStorage + albums deferred; per-Runner routing snapshots (no freezing, manual refresh); typed FSM patches; i18n context captured when a handler returns a method and when `bot(method)` is called, constructors i18n-free (D117, PD-07); butcher provenance; platform tiers; 3.x quick-win fixes; milestones A–J ([19](19-review-resolutions.md)) |

## The one-paragraph finding

Six analysis passes (models, routing, FSM, network, utils, PyO3/pydantic practice) agree: Rust pays
off where aiogram does **coarse-grained, CPU-bound work on data** — turning JSON into objects and objects
into JSON, holding them in memory, and rendering entities. It does **not** pay off where aiogram calls
user code: every filter, middleware and handler is a Python awaitable, so a Rust dispatcher can only speed
up the glue between them (≈1–3 µs/update) while asyncio↔tokio bridging costs tens of µs per await.
FSM and HTTP are I/O-bound. Several of the largest measured costs today are plain Python bugs that are
fixed in minutes, not by a rewrite.

## Where the time and memory go today (per update)

| Area | Today | Main cause | Fix | Doc |
|---|---|---|---|---|
| Parse realistic `Update` (2.5 KB JSON → 30 models) | 84 µs, **42.5 KB** RAM | per-object `model_post_init` (bot binding), `Literal[Enum]` Python callbacks, 130-slot `__dict__` per `Message` | Rust-native lazy types | [01](01-models.md) |
| `import aiogram` | **1.4 s**, 161 MB RSS | import-time `model_rebuild` loop over 665 classes | 3.x: drop loop; v4: no schema build at all | [01](01-models.md) |
| Re-mount Update for another bot | 179 µs | `model_dump` + `model_validate` round-trip | new bound view, O(1) (D103) | [01](01-models.md) |
| Dispatch, 52 handlers, F filters | 1 720–1 916 µs (worst case) | **`F` filters routed through `asyncio.to_thread`** (43 µs each) | 3.x bugfix → 215 µs; compiled routing snapshot → ~60–90 µs *est.* | [03](03-routing.md) |
| Dispatch fixed overhead | 21.6 µs (+8.6 µs FSM) | middleware chains rebuilt per call (38%) | prebuilt chains | [03](03-routing.md) |
| FSM `MemoryStorage` | 537–657 B per user, unbounded | defaultdict creates records on read; lock table never pruned | `.get()`, pruning | [04](04-fsm.md) |
| Outbound `SendMessage` encode | 93 µs | recursive Python `prepare_value`, urlencoded JSON-in-form | JSON body (3.x, 21 µs); Rust encoder (v4) | [05](05-network.md) |
| Inline keyboard builder | 30 btn: 4.4 ms; 100 btn: 46 ms | `deepcopy` per `add()` → O(n²) | shallow copy (3.x) | [06](06-utils.md) |

## Target architecture

```
                    ┌──────────────────────────── aiogram (Python) ────────────────────────────┐
user code ─────────▶│ Dispatcher / Router / filters / middlewares / DI   (routing snapshot)    │
                    │ FSM (thread-safe MemoryStorage, Redis, PyMongo-async), Scenes             │
                    │ Bot, BaseSession, AiohttpSession, webhook handlers (aiohttp + ASGI)       │
                    │ generated: shortcuts glue, enums (StrEnum), .pyi stubs, ErrorReason        │
                    └───────────────▲───────────────────────────────────────▲──────────────────┘
                                    │ coarse sync calls only                │
                    ┌───────────────┴─────────── aiogram._core (Rust/PyO3) ─┴──────────────────┐
                    │ generated #[pyclass(frozen)] types + methods  (sparse, lazily materialised)│
                    │ decode: bytes → Update / Response[T]   (serde/jiter, no Python per field) │
                    │ encode: method + bot defaults → JSON body | multipart parts               │
                    │ entities: UTF-16 math, HTML / MarkdownV2 render                            │
                    │ pydantic interop (__get_pydantic_core_schema__), pickle, to_json/from_json…│
                    └──────────────────────────────────────────────────────────────────────────┘
                                    ▲
             butcher (Rust, xtask) ─┘  HTML docs + OpenAPI 3.2 + errors.json + overlay → IR → emitters
```

The entity kernel renders only (UTF-16 offsets, HTML / MarkdownV2 unparse, owned by D-17); "parse" was dropped from
this box because nothing in 4.0 consumes it (PD-15, 06 §1).

Rules that follow from the research (detail in [08](08-build-release.md)):
- Rust exposes **synchronous, coarse-grained** functions. No `pyo3-async-runtimes`, no tokio, no
  `experimental-async`. asyncio orchestration stays in Python.
- Every pyclass is `frozen` + `Sync`; mutation goes through explicit, locked APIs.
- Python extension points stay Python: `BaseSession`, `BaseMiddleware`, `Filter`, `BaseStorage`,
  `BaseEventIsolation`, `KeyBuilder`, `TextDecoration` subclasses, `bot.call(...)` for unreleased methods (D96), `CallbackData`.

## Documents

| Doc | Content |
|---|---|
| [01-models.md](01-models.md) | Rust-native types: layout, laziness, bot binding, serialization API, extensibility |
| [02-butcher.md](02-butcher.md) | Rust generator, HTML + OpenAPI 3.2 adapters: inputs, overlay, IR, emitters, diffing |
| [03-routing.md](03-routing.md) | Dispatcher redesign in Python: per-Runner routing snapshots (D114) |
| [04-fsm.md](04-fsm.md) | FSM: thread-safe storage & isolation, Redis/Mongo |
| [05-network.md](05-network.md) | Session, encoder/decoder, webhook, errors |
| [06-utils.md](06-utils.md) | Entities/formatting in Rust; everything else stays Python |
| [07-free-threading.md](07-free-threading.md) | No-GIL support plan and dependency readiness |
| [08-build-release.md](08-build-release.md) | PyO3/maturin layout, wheels, CI, contributor workflow, best practices |
| [09-3x-quick-wins.md](09-3x-quick-wins.md) | Pure-Python fixes to ship in 3.x now |
| [10-forward-compatibility.md](10-forward-compatibility.md) | New API data never breaks a bot: tolerant unions/enums, per-update isolation, raw access |
| [11-removals.md](11-removals.md) | Legacy/compat code removed in 4.0 (2.x leftovers, pydantic-only APIs, dead code) |
| [19-review-resolutions.md](19-review-resolutions.md) | Resolutions of the independent review (D103–D121 + applied fixes), folded into the pages above (A-02); kept as history and index |
| [codex-review.md](codex-review.md) | Independent review (R01–R30), kept as the review artifact |
| [12-runtime.md](12-runtime.md) | Runner, update sources (Poller, webhook, ASGI, user-defined), runtime multi-bot add/remove, compat wrappers |
| [13-aiogram-rust-review.md](13-aiogram-rust-review.md) | Review of the community port `andrew000/aiogram_rust`: numbers, what we borrow (B1–B25), where we differ |
| [14-testing.md](14-testing.md) | Testing World toolkit (PR #1887): what it is, D51–D54, port plan to 4.0 |
| [15-observability.md](15-observability.md) | Trace hook, OpenTelemetry integration, structured logging, token redaction (D63–D66) |
| [16-support-policy.md](16-support-policy.md) | Deprecation policy, 3.x support window, migration bridges (D71–D74) |
| [17-cli.md](17-cli.md) | Built-in CLI (D75–D78) |
| [18-docs-migration.md](18-docs-migration.md) | Docs structure, API reference, translation, 3→4 migration guide (D79–D82) |

## Breaking changes in 4.0 (planned)

1. Types and methods are no longer `pydantic.BaseModel` subclasses. `isinstance(x, BaseModel)` is false.
   Native API instead (D91): `to_json()`, `to_dict()`, `from_json()`, `from_dict()`, `replace()` / `copy.replace`,
   `model_*` remain as deprecated aliases for the common kwargs, except `model_fields`, which is removed (D95). Kept: `==`, `repr`, pickle, use as a field
   in user pydantic models (incl. JSON schema). Gone: pydantic validators on aiogram types, `validate_assignment`.
2. All types are immutable (D15), including the 16 former `MutableTelegramObject`s (keyboards, `InputMedia*`,
   `MessageEntity`). Changes go through builders (`InlineKeyboardBuilder` etc.) or `obj.replace(...)`.
3. Subclassing a type is allowed, but decoded updates contain the base classes unless the subclass is
   registered (`aiogram.types.register(...)`). Model semantics are decided in 01 §3.6:
   - secondary bases work through ABC registration (D83);
   - equality needs the same class and equal data (D84);
   - ambiguous unions are resolved by tag or overlay predicate, otherwise `Unknown`; malformed members of decoded unions become `Unknown` with `.decode_error` (D85/D107);
   - nesting deeper than 128 levels is a decode error.
4. Each Runner routes on an immutable **snapshot** compiled at start (D114). `include_router` / `register` /
   middleware changes after start don't affect a running Runner until restart or `runner.refresh()`; a one-time
   warning is emitted. Nothing raises.
5. Free-threaded builds supported on 3.14t+ only; PyPy best-effort.
6. `MongoStorage` (motor) is removed; `PyMongoStorage` (already in 3.x) remains.
7. Installing from sdist needs a Rust toolchain.
8. All fields/entities deprecated during 3.x are removed (compat-ledger reset, [02](02-butcher.md) §4), e.g.
   `reply_to_message_id`, `disable_web_page_preview`, the 7.3 `Chat.*` fields now on `ChatFullInfo`.
9. Every union gains an `Unknown…` member; `Update.event_type` returns unknown type names instead of raising;
   undecodable and unknown-type updates go to `router.unknown_update`, and decode failures are also reported to `errors` with `phase=DECODE` (D49), instead of stalling polling ([10](10-forward-compatibility.md)).
10. API errors get `e.reason` (`ErrorReason` enum generated from `errors.json`, D47); exception classes are
   unchanged, so `except TelegramBadRequest` keeps working. `RestartingTelegram` is removed.
11. Legacy removals ([11](11-removals.md)):
    - `Message.content_type` and `ContentType` (use `F.photo`, `F.text | F.sticker`).
    - `event_from_user` / `event_chat` / `event_thread_id` kwargs (use `event_context`).
    - `aiogram.utils.markdown`.
    - `UNSET_*` sentinels, the flat `link_preview_*` fields on `DefaultBotProperties`.
    - `BaseFilter`, `CancelHandler`, `REJECTED`, `dp[...] = ...` writes.
    - Class-based handlers (`aiogram.handlers`, D42).
    - `utils.mixins`, `deep_linking` re-exports.
12. `CallbackData` is no longer a pydantic model (same declaration syntax; pydantic `Field`/validators must
    migrate). aiogram no longer depends on pydantic; the interop hooks work if the user installs it.
13. Compiled filter rejectors (03 §3): when a `Command` / `F.x == literal` filter is certainly false, the handler
    is skipped without running its other filters, including user filters placed before it. Filters with side
    effects must not rely on running for handlers that can't match.
14. `aiogram_i18n` is deprecated in favour of the core i18n (D25); the migration guide maps its API one to one.
15. Event isolation is **on by default** (D28): updates sharing an FSM key run one after another, so a slow
    handler delays that user's next update. Handlers that wait for a *later* update of the same key ("ask and wait"
    helpers, re-entrant `feed_update`) must use `async with state.release_isolation():` (D110) or they deadlock;
    re-entrant acquisition of the same key in the same task raises `RuntimeError` instead (PD-26).
    Pass `events_isolation=DisabledEventIsolation()` for 3.x behaviour.
16. Sync filter functions run **on the event loop** by default (D34), no longer in a thread. Wrap blocking ones
    with `blocking(fn)`, or pass `Dispatcher(sync_filters=SyncFilterMode.THREAD)` for the 3.x behaviour. Sync handlers are unchanged.
17. Error handlers bubble (D48): an error goes to the `errors` handlers of the router where it was raised, then to
    its parents. Handlers in sibling routers no longer catch it; move cross-cutting error handlers to a common
    parent or the dispatcher.
18. `model_dump_json()` (deprecated alias of `to_json()`) emits **wire names** (`from`, not `from_user`) and ignores
    `by_alias` (D86/D94). `model_dump()` keeps 3.x names while it exists.
19. Extra fields must be JSON-shaped (D87): `Message(..., tag=object())` raises `TypeError`.
20. Custom `TelegramMethod` subclasses are not supported (D96): call unreleased methods with
    `await bot.call("methodName", {...}, returns=Type)`; the migration checker flags existing subclasses.
21. **All generated API calls are keyword-only** (D100): `message.answer("hi")` → `message.answer(text="hi")`,
    `bot.send_message(1, "hi")` → `bot.send_message(chat_id=1, text="hi")`. `aiogram migrate fix` rewrites them.
22. `obj.as_(bot)` returns a **new bound view** instead of rebinding `obj` (D103): `m = m.as_(bot)` and every
    shortcut keep working; a bare `m.as_(bot)` statement no longer changes `m` (the checker flags it).
23. Collection fields are **tuples** (D106): `msg.entities == [e]` is false, `.append` fails; compare with tuples.
24. Outer middlewares of routers that hold no matching handler are **skipped** (D111), and an outer middleware
    that replaces the event does not change routing. Middleware that must see every update belongs on `dp.update`.

## Roadmap (milestones, D121)

Full 4.0 feature set, delivered as separately reviewable milestones, each with its own exit gate. The full D121 set
(A–J, including G and H) **blocks 4.0 GA** (PD-01). B is the binding go/no-go (D104). `4.0.0a1` is an alpha, not GA;
the 3.x support clock (D73) starts at **4.0.0 GA**. A few prerequisites are pulled ahead of their milestone (PD-31):
B-01 (build skeleton), I-12 (registry machinery), H-01 / H-02 (logging, redaction), H-05 (trace interface) and H-19
(MockedBot port). Task breakdown: [`../plans/`](../plans/README.md).

| Milestone | Deliverable | Exit gate / dependencies |
|---|---|---|
| **A — Contracts & baselines** | 19 resolutions applied to all pages (A-02); behaviour oracle = an **external pinned 3.x venv**, no in-tree reference path (PD-12); pinned benchmark inputs; corpus, bench harness and oracles authored on `dev-3.x` and merged forward (PD-12); independently safe 3.x fixes ([09](09-3x-quick-wins.md), D120). The public tree carries nothing that names or describes an unfixed security issue before its fix ships (PD-34) | oracle + benchmarks exist before any optimisation |
| **B — Model spike** (≈3 wk) | ~12 types incl. wide `Message`, Unknown variants, bound views (D103), cache seeding, GC, subclassing, `SendMessage` encoder, 2–3 `*_ext.rs` helpers | gate vs optimised 3.x, warm on pyo3 ≥0.30, Linux + macOS: parse ≥3×, memory ≥4× (incl. accessed trees and a child retained from a batch), first access ≤2×, warm access ≤1.6×, end-to-end dispatch no slower; `getUpdates` batch + `sendMessage` response paths (B24); cache/GC/teardown tests pass. **Fail → redesign the model layer** |
| **C — Reproducible butcher** | per-adapter IR + manifest (D118), overlay/ledger, generated types/methods/stubs, rename rule (D109) | offline emit deterministic; historical diffs, a new union, a name collision and an unsupported `send_copy` content all handled |
| **D — Client & wire** | JSON/multipart, raw calls (D96), defaults, custom sessions, webhook replies (R18), download/upload lifecycle | request/response differential cases with difference manifests (R26), hook compatibility, cancellation/resource tests |
| **E — Routing & runtime** | compiled routing snapshots (D111, D114), Runner `feed`/`process` + admission (R12), errors (D47–D50, D112) | routing differences match the decisions; lifecycle fault injection; multi-Runner tests |
| **F — FSM & scenes** | default isolation + `release_isolation` (D110), atomic merge, typed data (D115), history batching | race tests on 3.14t; application lost-update limits documented |
| **G — User-facing additions** | Depends, i18n/formatting (D117), retry/rate limit (R19), commands sync, CLI | own contract tests each; depends on stable E/F/D boundaries |
| **H — Testing & observability** | Testing World port, trace hook (D63, R23), OTel, logging/redaction (R22) | production code exercisable without the fake; all redaction and tracer-failure tests |
| **I — Distribution & migration beta** | Tier-1 wheels (D119), installed-wheel typing, sdist, import-free docs (R29), codemod/checker (R28), examples | fresh-machine install and 3→4 migration rehearsals across Tier 1 |
| **J — GA** | complete feature inventory, migration guide, release notes, published 3.x support dates | beta feedback resolved; **no unresolved P1 contract**; release ownership documented |

Dependency graph: binding semantics (B) precede the fake's identity (H); runtime scopes (E) precede Depends (G);
codec/default contracts (D) precede lazy formatting and retries (G).

## Open questions

No open *decisions* here. The review's contract questions were resolved in [19](19-review-resolutions.md) (D103–D121),
and planning-time owner decisions are PD-01..PD-34 in the [plans README §1](../plans/README.md#1-planning-decisions-normative-for-all-plans);
both are folded into these pages. Open owner questions during implementation are tracked in the plans
([`_DECISIONS.md`](../plans/_DECISIONS.md)). What remains is measurement in milestone B and the watch items. O1, O4,
O5 and O6 became D17–D20; O2 became D11, O3 became D15; O8 (built-in CLI) became D75–D78. O7 (schema source lag) is a
watch item, not a decision, and moved to [02](02-butcher.md) §6 Risks.
