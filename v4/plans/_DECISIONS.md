# Open owner decisions collected from the plans

Each line is a `Decide …` checklist item with its proposed default. Owner answers go into the plan's *Notes* (and README §1 when they affect several plans).

## [3x-07](3x-quick-wins/3x-07-drop-model-rebuild-loop.md) — Import time: drop the import-time `model_rebuild` loop
- Decide the mechanism (a/b/c) by prototype and measurement. Proposed default: (a) if it costs < 5 ms on first

## [3x-08](3x-quick-wins/3x-08-butcher-literal-tags.md) — Butcher: `Literal["x"]` tag fields; measure-or-drop the `RichTextUnion` field discriminator
- Decide where the change lives. Proposed default:

## [3x-09](3x-quick-wins/3x-09-json-request-body.md) — JSON request body when there are no files
- Decide the default `json_dumps`:

## [3x-13](3x-quick-wins/3x-13-deserialize-no-ssl-context.md) — `deserialize_telegram_object`: no SSL context per call
- Decide the mechanism. Proposed default: build the fake `Bot` per call with

## [3x-18](3x-quick-wins/3x-18-unknown-union-fallback.md) — `Unknown` fallback variant for discriminated unions (optional)
- Decide whether the change lives in the butcher tool or the `.butcher` config (as in 3x-08). Proposed default:

## [3x-20](3x-quick-wins/3x-20-deprecation-machinery.md) — Deprecation machinery backport (warning classes, filter, registry reader)
- Decide what happens to an application's code-level filter set **before** `import aiogram` (for example

## [3x-23](3x-quick-wins/3x-23-mutation-ledger-warnings.md) — Mutation warnings and Bot API ledger-field warnings
- Decide the ledger-field mechanism. Proposed default:

## [A-05](A-contracts/A-05-bench-harness.md) — Benchmark harness and method
- Decide the tool. Proposed default: a **stdlib harness** (as above). pytest-codspeed counts instructions and

## [B-00](B-spike/B-00-freeze-gate-spec.md) — Freeze the gate spec
- Decide how parse ratios are scoped (proposed default: **each** gated decode workload passes ≥3× on its own on
- Decide what first access is compared to (proposed default: native first read of a fixed access path, which
- Decide the memory estimator (proposed default: per-update bytes = peak-RSS delta of a fresh subprocess holding
- Decide the memory workloads and their gating (proposed default: **gated ≥4×**: untouched retained updates,
- Decide which child is retained (proposed default: one `Message` kept from a 100-update `getUpdates` batch, the
- Decide what "no slower" means for dispatch (proposed default: native median ≤ baseline median **and** the upper
- Decide the gating of the other benchmarks in 01 §5.2 (proposed default: informational, with two hard floors.
- Decide the estimator and run protocol: median of 7 runs, GC off, A/B in one machine session, raw samples kept,
- Decide the interpreters (proposed default: gated on CPython 3.13 and 3.14. 3.11 and 3.14t are informational, so

## [B-01](B-spike/B-01-crate-maturin-skeleton.md) — Crate + maturin skeleton + minimal CI
- Decide the version source (proposed default: keep `aiogram/__meta__.py` as the source of truth that

## [B-03](B-spike/B-03-decode-runtime.md) — Decode runtime core: field tables, value kinds, sparse layout
- Decide duplicate JSON keys inside one object (proposed default: last wins, as `json.loads` and 3.x pydantic
- Decide JSON strings with lone surrogates (`"\ud800"`), which Python `str` accepts but Rust `str` cannot hold
- Decide input aliases (`from` / `from_user`, `bot` / `bot_user`, B17) (proposed default: accepted by

## [B-04](B-spike/B-04-spike-type-set.md) — Spike type set (hand-written in emitted shape)
- Decide how out-of-set field types are represented (proposed default: the `Message` / `Update` field tables are

## [B-06](B-spike/B-06-value-semantics-native-api.md) — Value semantics + native serialization API
- Decide seeding when a passed instance is **bound** (proposed default: seed only when the passed object's
- Decide pickling a **bound** object (3.x raises, 19 corrections) (proposed default: pickle drops the binding and
- Decide pickle of registered subclasses with user state (proposed default: `__reduce__` uses `type(obj)`, so
- Decide `timedelta` in *type* DateTime fields (proposed default: rejected with `TypeError`, because 3.x pydantic

## [B-08](B-spike/B-08-subclassing-register.md) — Subclassing + `register`
- Decide how a registered Python subtype is instantiated from Rust (proposed default: allocate through the
- Decide `register` after decoding has started, on a free-threaded build (proposed default: allowed. Copy-on-write

## [B-10](B-spike/B-10-ext-helpers-stub-workflow.md) — `*_ext.rs` helpers + stub workflow
- Decide whether to run the 08 §2 glue-crate experiment (proposed default: no, unless the incremental debug

## [B-11](B-spike/B-11-cache-gc-teardown-ft-tests.md) — Cache / GC / teardown / free-threading tests
- Decide whether the TSan job is added now (proposed default: yes, scheduled weekly, non-blocking, owned by I-03

## [B-12](B-spike/B-12-dispatch-harness.md) — End-to-end dispatch harness
- Decide what to do if the A-10 realistic router's handlers call the API (proposed default: replace those calls
- Decide whether outer middlewares from the realistic router stay (proposed default: yes, as in the A-10

## [C-01](C-butcher/C-01-crate-xtask-ir-snapshot.md) — butcher crate, xtask entry point, IR model, snapshot format
- **Decide snapshot retention** (proposed default: commit **only the current API version's** snapshot directory

## [C-03](C-butcher/C-03-html-adapter.md) — HTML adapter
- **Decide the adapter fixture policy** (proposed default: tests use **small hand-written HTML excerpts** under

## [C-06](C-butcher/C-06-overlay-schema-loader.md) — Overlay schema and loader
- **Decide the file layout** (proposed default: one file per kind as in the table, with `shortcuts/` and `enums/`

## [C-07](C-butcher/C-07-fill-dsl.md) — Fill-DSL for shortcuts
- **Decide the fill-DSL grammar** (proposed default: the grammar above, i.e. paths, `?.` optional chaining,
- **Decide the guard exception type** (proposed default: keep `AssertionError` with the legacy message, matching 3.x,

## [C-08](C-butcher/C-08-merge-cross-check.md) — Merge and cross-check
- **Decide "unchanged entity"** (proposed default: the entity's IR node, with docs stripped, hashed **together with
- **Decide merge precedence** (proposed default: a structural discrepancy never auto-resolves and needs an overlay pin.

## [C-09](C-butcher/C-09-resolution-passes.md) — Resolution passes: D18 twins, D109 names, union classification
- **Decide request-only twin fields vs the 4.0 ledger reset** (02 §3 item 7 says request-only fields such as
- **Decide how the reserved-name set is built** (proposed default: **derived**, not hand-listed. It is the union of

## [C-10](C-butcher/C-10-ledger-diff.md) — Compat ledger and `butcher diff`
- **Decide the window's version half** (README D6 / 02 §4 say "2 Bot API **major** versions". Bot API majors have

## [C-15](C-butcher/C-15-bot-methods-emitter.md) — `_BotMethods` mixin emitter
- **Decide the old-param translation scope** (proposed default: implement only the emitter path with a fixture test.

## [C-16](C-butcher/C-16-router-observers-update-tables.md) — Router observers mixin and update tables (Python)
- **Decide where `event_type` lives** (02 §5 lists `Update.event_type` among the Python-emitted sites, 11 §1 says "computed in Rust"). Proposed default: `Update.event_type` / `event` in **Rust** (C-19), and the event-context table in **Python** (this task). Record it in Notes and flag it to the owner.

## [C-17](C-butcher/C-17-utility-signature-emitter.md) — Builder and utility signature emitter (D59)
- **Decide the generated module shape together with G-11** (proposed default: generated Python **mixin** modules

## [C-19](C-butcher/C-19-rust-forward-compat-emitter.md) — Rust forward-compat emitter: unions, `Unknown…`, enums, `Update.event_type`
- Decide keep-or-remove of the public `aiogram/utils/chat_member.py` module (proposed default: remove it and its

## [C-23](C-butcher/C-23-check-offline-determinism.md) — `butcher check`, offline determinism and the PR CI job
- **Decide how the formatter version is pinned** (proposed default: `check` runs `uv run --locked ruff format` so

## [C-25](C-butcher/C-25-historical-scenario-tests.md) — Historical diff and scenario tests (milestone C exit gate)
- **Decide the historical fixture policy** (proposed default: commit the converted IR fixtures **zstd-compressed** under

## [D-01](D-client/D-01-default-bot-properties-and-bot-cleanup.md) — Frozen `DefaultBotProperties`, `Bot` cleanup, `Bot.__repr__`
- Decide whether reassigning `bot.default = DefaultBotProperties(...)` is supported (proposed default: yes; the

## [D-02](D-client/D-02-exceptions-error-reason-restarting-removal.md) — Exceptions: `ErrorReason` on `e.reason`, `RestartingTelegram` removal, `ClientDecodeError.raw`
- Decide what `ClientDecodeError.raw` holds when the envelope itself is not JSON (proposed default: the full

## [D-03](D-client/D-03-token-safe-network-errors.md) — Token-safe network errors (`from None`, `.original`, redacted URLs)
- Decide how a network error states whether the request was sent (needed by G-13 to distinguish known

## [D-04](D-client/D-04-drop-aiofiles-input-file-replayable.md) — Drop `aiofiles`; add `InputFile.replayable`
- Decide the default `replayable` for user subclasses of `InputFile` (proposed default: `False`, so unknown

## [D-05](D-client/D-05-download-lifecycle.md) — Download lifecycle: per-phase timeouts, `bot.stream()`, typed overloads
- Decide `DownloadTimeout` defaults (proposed default: `connect=30`, `sock_read=60`, `total=None`) — record in
- Decide the `stream_content` compatibility shim for custom sessions whose override still takes `timeout: int`

## [D-06](D-client/D-06-request-middleware-manager.md) — Request middleware manager: prebuilt chain, `before=`/`after=` anchors, per-call request context
- Decide the per-call carrier (the only Decide item for it; D-10 cites it): how the per-call `request_timeout`,

## [D-07](D-client/D-07-rust-encoder-json.md) — Rust encoder: JSON request body, `Default` resolution, value rules
- Decide whether `encode` releases the GIL (`py.detach`) for large bodies (proposed default: no; 08 §7 rule 7

## [D-08](D-client/D-08-rust-encoder-multipart.md) — Rust encoder: multipart bodies and file extraction
- Decide attachment naming (proposed default: deterministic `file0`, `file1`, … in field-walk order; listed as an
- Decide whether a top-level file field is sent as `photo=attach://file0` + part `file0` (3.x behaviour) or as a

## [D-09](D-client/D-09-response-decoder.md) — Response decoder: `Response[T]` without pydantic, `getUpdates` per-update isolation
- Decide the Python-visible return shape of `decode_response` (proposed default: returns the result on success;

## [D-11](D-client/D-11-session-on-new-codec.md) — `BaseSession` / `AiohttpSession` on the Rust codec
- Decide how HTTP status and response info reach request middlewares on success (H-07 records

## [D-12](D-client/D-12-custom-session-hook-compatibility.md) — Custom-session hook compatibility (`prepare_value`, `check_response`, third-party sessions)
- Decide the `prepare_value` slow path (proposed default: when overridden, the encoder first produces the wire
- Decide the `check_response` contract (proposed default: signature unchanged except `content: bytes | str`

## [D-13](D-client/D-13-raw-bot-call-raw-method.md) — Raw `bot.call(...)` and internal `RawMethod`
- Decide what `aiogram.Raw` is (proposed default: a public type alias

## [D-15](D-client/D-15-request-response-differential-cases.md) — Request/response differential cases with difference manifests (D exit gate, part 1)
- Decide which 3.x tag the oracle pins for D (proposed default: the A-06 "optimised" tag that includes 3x-09 /

## [D-17](D-client/D-17-rust-entity-rendering-kernel.md) — Rust entity-rendering kernel: UTF-16 offsets, HTML/MarkdownV2 unparse and quoting
- Decide the formatting-tree render input shape with G-08 (proposed default: a flat pre-order list of

## [E-01](E-runtime/E-01-dispatcher-filter-removals.md) — Dispatcher and filter legacy removals
- **Decide the fate of the documented-but-never-set `event_business_connection_id`** (proposed default: remove

## [E-02](E-runtime/E-02-dispatch-table-executor.md) — Compiled `DispatchTable` and executor
- Decide when routing keys are computed (proposed default: **after the `dp.update` outer chain**, at the routing

## [E-03](E-runtime/E-03-snapshot-lifecycle.md) — Routing snapshot lifecycle: topology epoch, caching, refresh, mutation warning
- Decide which snapshot `dp.feed_update()` uses when called **inside** an update processed by a Runner (re-entrant
- Decide what a mutation of a user object *inside* the snapshot means, e.g. a filter instance's attribute

## [E-04](E-runtime/E-04-router-graph-multi-parent-flags.md) — Router graph: multiple parents, diamond check, router-level flags
- Decide what `data["handler"]` is once flags are merged per path (proposed default: a frozen per-snapshot

## [E-09](E-runtime/E-09-routing-keys-compiled-rejectors.md) — Routing keys and compiled rejectors (prefilter, literal and command index)
- Decide how rejectors treat a registered subclass that overrides a routed property such as `text` (R10;

## [E-11](E-runtime/E-11-error-model-bubbling.md) — Error model: `ErrorEvent` fields, phases, bubbling, update-scope hooks
- Decide the policy when an `errors` handler itself raises (R17; proposed default: the new exception is **not**

## [E-12](E-runtime/E-12-runtime-errors.md) — `dp.runtime_errors` observer
- Decide how code that has no dispatcher at hand reaches `runtime_errors`, e.g. `RetryMiddleware` running in a

## [E-13](E-runtime/E-13-runner-lifecycle-bot-registry.md) — `Runner`: lifecycle state machine, sources, task set
- Decide sources attached after start (proposed default: started immediately; `runner.detach(source)` stops it,
- Decide user `CancelledError` handling inside hooks (proposed default: cancellation of `start()`/`stop()` still
- Decide whether "one Runner per loop" is enforced (R11) (proposed default: not enforced globally; at most one

## [E-14](E-runtime/E-14-feed-paths-forward-compat-dispatch.md) — Feed paths (`runner.feed` / `runner.process`, `dp.feed_update`) and forward-compatible dispatch
- Decide what event object `unknown_update` handlers receive (10 §3 Layer 1 says `UnknownEvent(type, raw)`,
- Decide the order of `errors(phase=DECODE)` and `unknown_update` and the rule when either fails (R13)
- Decide `DecodePolicy` precedence (proposed default: `Dispatcher` policy governs update decoding on every feed
- Decide the fate of user `@dp.update()` handlers (in 3.x they ran only when `_listen_update` raised `SkipHandler`

## [E-15](E-runtime/E-15-poller.md) — `Poller` update source
- Decide the offset on **stop** (12 §5 only specifies removal; 3.x redelivers the last batch after a restart)
- Decide how `handle_as_tasks=False` maps onto the Runner (proposed default: the Poller calls

## [E-16](E-runtime/E-16-webhook-core-aiohttp-sources.md) — Webhook core and aiohttp sources
- Decide the HTTP status matrix (codex R13) (proposed default: bad/missing secret → 401; unknown bot / token not
- Decide the default `max_pending` (proposed default: `4 × tasks_concurrency_limit`, or 1 000 when the limit is

## [E-17](E-runtime/E-17-asgi-app.md) — ASGI webhook app
- Decide the ASGI bot-lookup API (D24 names only the aiohttp classes) (proposed default:

## [E-20](E-runtime/E-20-typed-di-typeddicts.md) — Typed DI: base `TypedDict`s for handler and middleware data
- Decide the shape for **router-level** outer middlewares (`router.message.outer_middleware`), which see
- Decide the `bots` type (3.x `list[Bot]`; the Runner registry exposes a cached tuple, E-23) (proposed default:

## [E-22](E-runtime/E-22-single-bot-sharding.md) — Single-bot thread sharding (ingress Poller, per-worker queues)
- Decide where updates **without** an isolation key go (no user/chat: polls, some `chat_boost`/`purchased_paid_media`-
- Decide the per-worker queue size and overload behaviour (proposed default: `queue_size = tasks_concurrency_limit`
- Decide what removal/stop commits in sharded mode (proposed default: the ingress commits

## [E-23](E-runtime/E-23-bot-registry.md) — Runner bot registry: `add_bot` / `remove_bot`, `bot_added` / `bot_removed`, shared-FSM ownership
- Decide concurrent `add_bot` / `remove_bot` of the same bot (proposed default: operations on one bot id are
- Decide duplicate token identities (two `Bot` objects, same token) (proposed default: registry keyed by `bot.id`;
- Decide a failing `bot_added` hook (proposed default: reported to `runtime_errors` with `phase=BOT_HOOK`; the
- Decide whether one bot may belong to several sources (proposed default: no; one source per bot per Runner,
- Decide ownership of shared resources when several Runners share one Dispatcher (proposed default: remove

## [F-01](F-fsm/F-01-thread-safe-memory-storage.md) — Thread-safe `MemoryStorage` (one dict + one lock)
- Decide the nested-value aliasing contract (R14) (**proposed default:** copies stay **shallow at the top level**

## [F-02](F-fsm/F-02-isolation-lock-table-default-on.md) — Cross-thread, cross-loop isolation lock table, on by default (D28)
- Decide the R14 hand-off state machine (**proposed default:** waiter states `QUEUED → GRANTED → ACQUIRED`, plus
- Decide the startup warning for in-process isolation with a storage that provides `create_isolation()` (e.g.

## [F-03](F-fsm/F-03-release-isolation-warn-after.md) — `state.release_isolation()`, `isolation_warn_after`, release hooks, re-entrancy error
- Decide where `isolation_warn_after` is configured and which channel the warning uses (**proposed default:**

## [F-07](F-fsm/F-07-mongo-remove-motor-key-validation.md) — Mongo: remove motor `MongoStorage`; `PyMongoStorage` key validation, batching, single-loop
- Decide the scope of Mongo key validation (**proposed default:** validate **top-level** data keys in both

## [F-08](F-fsm/F-08-shared-converter-core.md) — Shared converter core (FSMData + CallbackData)
- Decide `Fraction` support (**proposed default:** support `Fraction` in both codecs, encoded as `str(value)`

## [F-09](F-fsm/F-09-fsmdata-typed-fsmcontext.md) — `FSMData` and the typed `FSMContext` API (typed patches, adapters protocol)
- Decide whether typed dumps are JSON-shaped in every storage, including MemoryStorage (**proposed default:**
- Decide how adapters reach a manually built `FSMContext` (**proposed default:** `FSMContext(storage, key,

## [F-11](F-fsm/F-11-callbackdata-without-pydantic.md) — `CallbackData` without pydantic (D14)
- Decide lax coercion when unpacking (**proposed default:** accept exactly what 3.x pydantic lax mode accepted for

## [F-13](F-fsm/F-13-scenes-d33.md) — Scenes (D33): batched history, copy-on-write, action warning, registry snapshot hook
- Decide when the missing-action warning fires (**proposed default:** only when the scene defines the action for

## [G-01](G-features/G-01-param-resolver-hook.md) — ParamResolver hook
- **Decide resolver precedence and multiple markers** (proposed default: resolvers are asked in
- **Decide what a claimed parameter does when its name is also in `data`** (proposed default: the resolver wins

## [G-02](G-features/G-02-depends-scope-teardown.md) — Built-in `Depends`, per-update scope and teardown
- **Decide the cache key vs the 3.x data scopes** (R09 keeps four scopes: update, router copy, observer-trigger,
- **Decide what happens when a middleware calls `handler` twice or concurrently** (D38 allows a second call).
- **Decide cancellation semantics.** The proposed default: on `CancelledError` the scope still tears down
- **Decide how multiple teardown failures are reported.** The proposed default: one `RuntimeErrorEvent` per
- **Decide what a provider failure during filter matching does.** The proposed default: the update is aborted
- **Decide the definition of "flag callables"** as a resolution site. 03 §5 lists them, but 3.x flags are data,

## [G-03](G-features/G-03-i18n-core.md) — i18n core: engines, context, managers, lazy values
- **Decide whether `i18n.key(**kw)` attribute access maps `_` to `-`** for Fluent ids (proposed default: yes,

## [G-05](G-features/G-05-utils-i18n-compat.md) — 3.x `aiogram.utils.i18n` compatibility layer
- **Decide the fate of `I18n.get_current()` / `I18n.set_current()`** (inherited from `ContextInstanceMixin` in
- **Decide the `i18n` data-key collision.** The 3.x middleware injects the `I18n` instance under `i18n_key`

## [G-06](G-features/G-06-lazy-text-capture.md) — Lazy text in display fields, with i18n context capture (D117 / PD-07)
- **Decide lazy-value semantics inside frozen types** (R21; 19 is silent). Proposed defaults:
- **Decide whether wire-decoded objects ever contain lazy values** (proposed default: never; only user-constructed

## [G-07](G-features/G-07-lazy-filter.md) — `LazyFilter`
- **Decide whether `LazyFilter` also matches `callback_query.data` / `caption`** (proposed default: text only, as

## [G-09](G-features/G-09-lazy-text-trees.md) — Lazy `Text` trees (D61)
- **Decide how bot-level `Default("parse_mode")` interacts with a lazy `Text`** (proposed default: a lazy `Text`
- **Decide whether a plain `L.key()` (not inside `Text`) in a field with `parse_mode="HTML"` stays legal**

## [G-10](G-features/G-10-utils-removals.md) — Utils removals and rewrites
- **Decide whether the WebApp dataclasses keep `model_*` aliases** (proposed default: no; they were never Bot API

## [G-11](G-features/G-11-generated-utils-signatures.md) — Generated utils signatures, immutable-output builders
- **Decide whether `MediaGroupBuilder.add(type=…)`'s positional/keyword shape changes** (3.x `add()` takes

## [G-12](G-features/G-12-commands-from-handlers.md) — Bot commands from handlers (D60)
- **Decide how conflicting descriptions are handled** (same command, same scope + language, different
- **Decide command order** (proposed default: DFS registration order of the router tree, first occurrence wins
- **Decide what "known languages" means for `delete_missing`** (proposed default: the union of languages in the
- **Decide whether `resolve_bot_commands` reads the live graph or a snapshot** (proposed default: the live
- **Decide whether `CommandStart(description=…)` opts in** (R30; proposed default: yes; `CommandStart` is

## [G-13](G-features/G-13-retry-middleware.md) — Opt-in `RetryMiddleware`
- **Decide the `max_wait` vs `isolation_warn_after` default clash.** Retry's default `max_wait=30` s inside a
- **Decide whether `max_wait` is per attempt or total** (R19). Proposed default: per attempt, plus an optional

## [G-14](G-features/G-14-rate-limit-middleware.md) — Opt-in `RateLimitMiddleware`
- **Decide the bucket key when one session is shared by several bots** (D45 docs show sharing a session).
- **Decide whether `per_group_per_minute` applies to channels** (proposed default: yes, all negative ids) —

## [G-15](G-features/G-15-cli-core.md) — Built-in CLI core (`aiogram`, `python -m aiogram`, plugins, `info`)
- **Decide plugin name-collision precedence** (R30). Proposed default: built-in commands always win; between

## [G-16](G-features/G-16-cli-run.md) — `aiogram run polling` / `aiogram run webhook`
- **Decide webhook setup failure and rollback** (R30). Proposed default: if `--set-webhook` fails for any bot,
- **Decide whether `run webhook --set-webhook` deletes the webhook on shutdown** (proposed default: no, unless
- **Decide whether `run webhook` authenticates the secret before creating on-demand bots** (R30). Proposed

## [G-17](G-features/G-17-cli-reload.md) — `--reload` via watchfiles
- **Decide `run webhook --reload` with `--set-webhook`** (proposed default: `setWebhook` runs only in the first

## [G-18](G-features/G-18-cli-bot-commands.md) — `aiogram bot` commands (me, webhook, commands sync)
- **Decide the `--managed` scope syntax** (proposed default: `default`, `all_private_chats`, `all_group_chats`,

## [G-20](G-features/G-20-aiogram-i18n-final-release.md) — `aiogram_i18n` → core mapping, and the final `aiogram_i18n` release
- **Decide what the final `aiogram_i18n` release does on aiogram 4** (proposed default: it declares
- **Decide the owner and the release date** (aligned with 4.0.0 GA) — record in Notes and hand to J-06.

## [G-21](G-features/G-21-aiogram-cli-final-release.md) — Final `aiogram-cli` release
- **Decide the final release's aiogram requirement** (the 1.x line pins `aiogram<4`). Proposed default: drop the
- **Decide the owner and the release date** (aligned with 4.0.0 GA) — record in Notes and hand to J-06.

## [H-05](H-testing-observability/H-05-trace-hook-core.md) — Trace hook core (protocol, calling rules, adapter)
- **Decide the SpanKind gaps** (proposed default: no new kinds in 4.0. Decode failures appear on the `UPDATE`

## [H-08](H-testing-observability/H-08-otel-traces.md) — `aiogram[otel]`: traces
- **Decide the default `exclude`** (proposed default: `SpanKind.FILTER` is excluded by default, because PR

## [H-09](H-testing-observability/H-09-otel-metrics.md) — `aiogram[otel]`: metrics with bounded labels
- **Decide the `router` label for unnamed routers.** 3.x `Router(name=None)` defaults to `hex(id(self))`,

## [H-10](H-testing-observability/H-10-testing-world-import.md) — Testing World import + packaging
- **Answered 2026-11-19 (see the plan's Notes): #1887 shipped in 3.x with the entry-point shim.** Was: Decide #1887's shipping status in 3.x (proposed default: #1887 does **not** merge into `dev-3.x`; the

## [H-11](H-testing-observability/H-11-generated-toolkit-tables.md) — Generated toolkit tables + fake-coverage guard
- **Decide `BOT_RIGHTS`.** Admin rights per method are not in the IR (proposed default: it stays hand-written

## [H-13](H-testing-observability/H-13-binding-identity-rewrite.md) — Binding and identity rewrite (bound views)
- **Decide per-receiving-bot identity** (proposed default: the promise is "`message is chat.messages[-1]` for

## [H-14](H-testing-observability/H-14-delivery-through-runner.md) — Toolkit delivery through the Runner
- **Decide sync fixture vs async lifecycle.** The 3.x `bot_env` fixture in `plugin.py` is sync and tears down

## [H-17](H-testing-observability/H-17-toolkit-feature-interop.md) — Toolkit interop with 4.0 features (flood/retry, Unknown, ErrorReason, i18n)
- **Decide where rejection texts live** (proposed default: they stay in `aiogram/test/rejections.py`, with

## [I-01](I-distribution/I-01-packaging-hardening.md) — Packaging hardening of the single `aiogram` distribution
- **Decide the version source of truth** (proposed default: `aiogram/__meta__.py` stays canonical for
- **Decide the unsupported-platform message** (proposed default: no custom build hook. maturin's own "Rust
- **Decide the MSRV promise** (proposed default: document "the Rust version pinned in `rust-toolchain.toml`

## [I-02](I-distribution/I-02-tier1-wheel-matrix-release.md) — Tier-1 wheel matrix and release workflow
- **Decide the release CI cost** (08 §5/§4: about 60–90 wheels × about 10 min). Proposed default: the full matrix runs only on

## [I-03](I-distribution/I-03-free-threaded-wheels-ci.md) — Free-threaded wheels and CI
- **Decide the published ft extras combinations** (proposed default: publish a table in the Install docs, with

## [I-05](I-distribution/I-05-pr-ci-structure-caching-coverage.md) — PR CI structure, caching and coverage
- **Decide the PR vs nightly matrix** (proposed default). Record the measured PR wall-clock in Notes and flag it to
- **Decide the stale "Python fallback encoder" wording** in 08 §5 ("request encoding, Rust vs the Python fallback

## [I-07](I-distribution/I-07-dependencies-extras-restructure.md) — Dependencies and extras restructure
- **Decide how to drop the pins that violate D70** (proposed default):

## [I-08](I-distribution/I-08-contributor-workflow.md) — Contributor workflow for `dev-4.x`
- **Decide prebuilt wheels for Python-only contributors** (proposed default: not in 4.0; rustup is a documented

## [I-14](I-distribution/I-14-migrate-engine.md) — `aiogram migrate` engine (check / fix)
- **Decide whether `aiogram migrate` may import `_core`** (proposed default: yes. `uvx --from 'aiogram[migrate]>=4'`

## [I-15](I-distribution/I-15-receiver-inference.md) — Receiver inference for the migrate tools
- **Decide which 3.x version the table tracks** (proposed default: the migration-baseline 3.x release cut by

## [J-07](J-ga/J-07-ga-cut-rtd-switch.md) — 4.0.0 GA cut and Read the Docs `latest` switch
- **Decide whether to switch the GitHub default branch to `dev-4.x` at GA** (proposed default: yes, at GA; `dev-3.x`
