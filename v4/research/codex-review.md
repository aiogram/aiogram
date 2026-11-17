# aiogram 4.0 Rust plan — independent review

Review date: 2026-11-17. Scope: `README.md` and all 18 numbered pages in this directory. This report is a review artifact, not an amendment to those decisions. No source decision page was edited.

The architecture is worth prototyping, but the pages are not yet a consistent implementation specification. The strongest choices are the coarse Rust data boundary, Python orchestration, generated API surface, per-update failure containment, and differential testing. The principal risks are object ownership and bot binding, observable routing changes hidden behind compatibility claims, lifecycle semantics across loops, and migration/storage guarantees that exceed the mechanisms specified.

Proceed with bounded prototypes and separately reviewable implementation parts. Do not treat the “None” under the README's open questions as an accurate statement of readiness. Keep the model spike gate binding. Keep the intended feature set for 4.0, as requested during this review, while giving each part its own acceptance gate.

## 1. Review method and limits

I read every page, compared cross-page contracts, inspected the current implementations explicitly referenced by the pages, ran small local behavior probes, and checked selected upstream documentation. Findings distinguish **confirmed** contradictions/behavior, **design gaps**, and **hypotheses requiring measurement**. Proposed code does not exist here, so a design risk is not a claim that an implemented v4 contains a demonstrated bug.

Local evidence came from checkout HEAD `b42c8c80acfe7f29a4a12a6a8eeaf07d1bb13917`, Python 3.13.7 on macOS arm64, installed aiogram metadata 3.31.0, pydantic 2.14.2, pydantic-core 2.50.2, and aiohttp 3.14.5. The planning directory was untracked at review time; HEAD alone therefore does not identify its contents. The SHA-256 of the sorted JSON mapping of the 19 source filenames to their SHA-256 hashes was `156dc420489159634b4951b86d713c7983703790c9906ad250f8eacfd0b10b00`.

The performance figures in the pages were not independently reproduced. In particular, the community port's build/benchmark results remain attributed evidence from [13](13-aiogram-rust-review.md), not results of this review. Attempts to retrieve its PR #11 and the staging OpenAPI JSON through the web tool failed; this does not establish that those resources are unavailable generally. Dependency-wheel claims were not exhaustively re-audited.

No network request was sent with a bot token. Behavior probes used fabricated local credentials and did not call Telegram. No implementation, dependency, changelog, or original decision page was changed. Full repository lint/test/docs builds are not evidence for the proposed architecture and were not run for this standalone report.

## 2. Interactive answers and their effect

These are the owner's answers during this review. They take precedence over recommendations that would assume a different product direction.

| Topic | Owner's answer | Consequence for this report |
|---|---|---|
| Review scope | Challenge every decision | Rust, packaging, removals, scope and support policy were all open to review. |
| Bot binding | Evaluate the trade-offs before deciding | No final binding contract was chosen. R02 compares alternatives and recommends independent bound views. |
| Delivery | Keep 3.x best-effort delivery; document it precisely | R13 does not demand durable or exactly-once processing. It requires precise loss/replay semantics. |
| Feature scope | Additive features are part of 4.0's value; implement them as smaller parts until the valuable parts are complete | The delivery plan retains the feature set and splits implementation milestones. It does not silently defer those features to 4.x minors. |
| Deprecated model aliases | Allow the changes in 4.0 with explicit documentation | R06 treats altered alias behavior as accepted breaking changes, not compatibility defects to undo. |
| Listed removals | Accept all listed removals to simplify 4.0 | The report challenges the evidence and migration machinery, but does not recommend restoring those APIs as a release prerequisite. |
| Validation policy | Use one permissive policy everywhere | R07 requires a precise common permissive contract; it does not impose a separate strict outbound default. |
| Model spike | Keep the gate binding; reconsider the model design if it fails | D4 and its dependent decisions must remain conditional until the gate passes. |

## 3. Priority and coverage

**P1** means resolve before implementing the affected public contract or relying on the safety claim. **P2** means resolve before beta/GA or before the affected optional feature ships. These are design-review priorities, not incident severities.

| Finding | Priority | Main issue |
|---|---|---|
| R01 | P1 | A binding spike gate needs a real architectural fallback. |
| R02 | P1 | Shared bot rebinding conflicts with ownership, identity and concurrency. |
| R03 | P1 | Python wrapper caches need interpreter-aware synchronization and GC design. |
| R04 | P1 | Sparse data alone does not establish the memory target. |
| R05 | P1 | Raw data, immutability, equality, hashing and pickle need one coherent model. |
| R06 | P1 | Accepted serialization breaks still lack a complete contract. |
| R07 | P1 | Permissive validation and extensibility have unresolved boundaries. |
| R08 | P1 | A real Bot API field already collides with `.bot`. |
| R09 | P1 | One dispatch dictionary changes failed-candidate data isolation. |
| R10 | P1 | Compiled rejectors and flattened routing need a semantic boundary. |
| R11 | P1 | Freeze lifetime and shared user objects are not covered by immutable tables. |
| R12 | P1 | Runner admission, lifecycle and ownership are underspecified. |
| R13 | P1 | Best-effort delivery must expose acknowledgement and failure behavior. |
| R14 | P1 | Default FSM isolation needs a cancellation-safe state machine. |
| R15 | P1 | Redis migration and atomic updates overpromise codec/TTL/cluster compatibility. |
| R16 | P2 | Typed FSM data is a substantial validation subsystem. |
| R17 | P1 | Depends and error handling disagree about teardown ownership. |
| R18 | P1 | File/default/lazy serialization prevents a universal JSON-only path. |
| R19 | P2 | Retry and rate-limit middleware need attempt-level semantics. |
| R20 | P1 | Album buffering conflicts with the stated middleware/isolation ordering. |
| R21 | P2 | Lazy i18n needs paired text/entities and stable request rendering. |
| R22 | P1 | Proposed token redaction misses child loggers and exception causes. |
| R23 | P2 | Tracing requires explicit failure, overhead and cardinality bounds. |
| R24 | P1 | Codegen needs reproducible source provenance and direction-aware schemas. |
| R25 | P2 | Build rules must be measured policies, not compiler invariants. |
| R26 | P2 | Testing needs explicit expected differences and independent oracles. |
| R27 | P1 | Several 3.x “quick wins” are not safe drop-in changes. |
| R28 | P2 | Migration and support promises are internally inconsistent. |
| R29 | P2 | Stub-based documentation needs a proven import-free build. |
| R30 | P2 | CLI/plugin and command-sync contracts need completion. |

Every page is covered:

| Page | Findings / assessment |
|---|---|
| [README](README.md) | R01, R06, R11–R13, R26, R28; useful architecture summary, inaccurate closure/readiness claim. |
| [01 models](01-models.md) | R02–R08, R18; highest concentration of unresolved public contracts. |
| [02 codegen](02-butcher.md) | R07–R08, R24–R25, R28–R29; strong IR boundary, incomplete reproducibility. |
| [03 routing](03-routing.md) | R09–R12, R17, R23; optimize only after the semantic oracle exists. |
| [04 FSM](04-fsm.md) | R14–R16, R20; sound Python placement, difficult concurrency/migration work. |
| [05 network](05-network.md) | R13, R18–R19; retain aiohttp and extension points, specify fallback behavior. |
| [06 utils](06-utils.md) | R20–R21, R27, R30; retain feature scope, separate its acceptance gates. |
| [07 free-threading](07-free-threading.md) | R02–R03, R11–R14, R25; memory safety and application concurrency are different promises. |
| [08 build/release](08-build-release.md) | R01, R24–R26, R29; packaging direction reasonable, support tiers need precision. |
| [09 quick wins](09-3x-quick-wins.md) | R27; do not merge the list wholesale as bugfixes. |
| [10 forward compatibility](10-forward-compatibility.md) | R05, R07, R13; resilience is valuable but cannot guarantee successful typed decoding of arbitrary future data. |
| [11 removals](11-removals.md) | R06, R08, R28; owner accepts removals; migration cost remains real. |
| [12 runtime](12-runtime.md) | R11–R13, R17–R20; central lifecycle boundary is useful, protocols need completion. |
| [13 community review](13-aiogram-rust-review.md) | R01, R04, R10, R25–R26; borrow measured lessons, not universal conclusions. |
| [14 testing](14-testing.md) | R02, R12, R26; keep typed interception, qualify the fake's fidelity. |
| [15 observability](15-observability.md) | R22–R23; concrete redaction defect needs correction before implementation. |
| [16 support](16-support-policy.md) | R06, R28; distinguish major-reset rules from rolling deprecations. |
| [17 CLI](17-cli.md) | R30; useful feature set, plugin transition is not transparent. |
| [18 docs/migration](18-docs-migration.md) | R28–R29; shared registry and tested examples are good choices. |

## 4. Models and the Rust boundary

### R01 — The model gate must control downstream decisions

**Confirmed inconsistency; P1.** [01 §5](01-models.md) says a failed spike falls back to optimized pydantic models with Rust codecs/entities. Meanwhile D4, D11, D14, D15, D53 and the native serialization API are presented as settled. The rejected “Rust decode → pydantic construction” approach also casts doubt on what the codec fallback actually means.

Keep a mandatory core as a hypothesis, not a conclusion justified by pydantic's packaging precedent. Many bots are network-bound; deployment size, contributor time and memory may matter more than microsecond parsing wins. The rejection of msgspec because it is C rather than Rust is a maintenance preference, not performance evidence. A narrow comparative prototype could test whether the desired memory/API gains require this much custom machinery.

**Resolution:** freeze numerical and semantic gates before the spike; include the cost of wrappers, raw retention, helper ports, wheels and warm dispatch. If it fails, reopen the dependent model/codegen/i18n/testing/packaging choices explicitly. Do not continue building a native-only API while calling pydantic a viable fallback. The owner confirmed that the gate is binding.

### R02 — Shared context, identity seeding and rebinding cannot all be unconditional

**Confirmed contract conflict; P1.** [01 §3.1–3.2](01-models.md) combines one mutable `Ctx` per tree, `as_(bot)` returning the same object, and `Update(message=m).message is m`. [14 D53](14-testing.md) also promises identity with objects retained in the testing world.

Consider one `Message` inserted into two updates destined for different bots. If both parents retain that same wrapper, it cannot simultaneously expose both bots. If its context is replaced, one parent or the original caller changes behavior. If contexts are not replaced, parent and child disagree. Even in a single loop, rebinding between two awaits can send a shortcut through the wrong bot. An atomic swap prevents a pointer race; it does not make the operation semantically isolated.

The current [BotContextController](../../../aiogram/client/context_controller.py) changes only the receiving object's `_bot`. A local probe confirmed that `update.message.as_(b)` leaves `update.bot` and `update.message.chat.bot` unchanged. Tree-wide rebinding is therefore a break, not the same existing contract. Current dispatcher remounting reconstructs a tree instead of mutating the original one.

| Choice | Benefit | Cost / limitation |
|---|---|---|
| Shared mutable tree binding | Cheap tree-wide rebinding; stable existing wrappers | Hidden mutation across aliases; unsafe logical reuse across bots/loops. |
| Binding per wrapper | Closest to current `as_()` | Subtree consistency and remounting need explicit traversal or new views. |
| Independent bound view over immutable data | O(1) root view creation; bindings cannot redirect each other | Child wrapper caches belong to the view; identity across differently bound views cannot be promised. |

**Recommendation:** independent bound views, with the shortcut capturing its bot when called. Retain identity within one view; restrict constructor cache seeding to compatible bindings or explicitly unbound construction. Do not let the fake world's identity promise dictate unsafe production ownership. Specify separate semantics for `as_`, `replace`, constructor composition and dispatcher remounting. This remains an owner decision.

**Acceptance:** two bots using the same immutable payload concurrently cannot redirect each other's shortcuts; parent/child binding behavior is specified and tested before and after child materialization.

### R03 — `OnceLock` is not sufficient proof of interpreter safety

**Verified upstream constraint and design gap; P1.** [01](01-models.md) states that `OnceLock` is safe under free-threading, while [07](07-free-threading.md) prohibits locks across Python callbacks. Initializing a cached Python wrapper, registered subclass or lazy value can execute Python or attach/detach from the interpreter. PyO3 supplies `PyOnceLock` specifically to avoid interpreter-related deadlocks; re-entrant initialization remains a separate hazard even with that primitive. [PyO3 synchronization documentation](https://pyo3.rs/main/doc/pyo3/sync/struct.PyOnceLock.html).

Cached `Py` children, a context-held `Bot`, lazy Python values and registered subclasses also introduce Python reference cycles. Iterative Rust deallocation and a JSON depth limit do not replace GC traversal. Shared Rust ownership of Python references requires particular care: document who owns and reports each edge, rather than independently reporting a single shared reference as though every wrapper owned it. [PyO3 GC integration](https://pyo3.rs/main/class/protocols.html).

**Resolution:** prototype cache initialization, re-entrancy handling, traversal/clearing, and interpreter teardown together. Process-global Python-object interning must be interpreter-aware, or subinterpreters must be explicitly unsupported. Pure Rust interning and Python-object interning are different mechanisms.

**Acceptance:** concurrent first access returns one wrapper; callback re-entry cannot deadlock; cycles through Bot/session/user state are collectable; teardown works on the lowest supported CPython and free-threaded builds.

### R04 — Measure wrapper caches and retained roots, not only Rust structs

**Measurement hypothesis; P1.** [01 §3.1](01-models.md) makes fields sparse but proposes a fixed `[OnceLock<Py<PyAny>>; N]` wrapper cache. For a wide `Message`, this is still storage proportional to the field count. Rust struct data, reference counts, Python wrappers, cached strings and raw bytes coexist.

A child that retains a tree context may also retain an entire update or response-batch raw buffer after the parent is discarded. The raw-slice optimization can trade allocations for retention. Repeatedly accessing `.raw` materializes another representation. These costs are absent from the community port's reported memory evidence.

**Resolution:** budget bytes separately for decoded data, cache metadata, materialized children, raw buffers and retained context. Consider sparse caches and independently owned update slices when measured retention warrants them. Do not prescribe one before measuring.

**Acceptance:** RSS/native-allocation measurements for untouched updates, ordinary handler access, fully materialized trees, `.raw`/`to_dict()` use, and retaining only one nested child from a 100-update batch. `tracemalloc` alone cannot establish total native memory. Include GC-on sustained runs as well as microbenchmarks.

### R05 — Raw access, value semantics and persistence need a single contract

**Confirmed inconsistencies and gaps; P1.** [10 §3](10-forward-compatibility.md) defines `.raw` as a cached mutable dictionary for the whole object. [01 §4](01-models.md) says exposed containers are fresh copies or tuples. Those are different contracts. The pages also alternate between raw unknown-field storage and the entire original object.

Specify the following before implementing:

- Whether `.raw` is a fresh deep builtins tree, a read-only view, or shared mutable state. Mutating diagnostic raw data must not silently change equality or a future request.
- What `.raw_json` means for constructors, `from_dict`, `replace`, and objects with lazy text/files/default sentinels. “Exact bytes received” only applies to wire-origin objects.
- Whether `replace(text=...)` preserves original diagnostic bytes, produces new canonical bytes, or exposes both separately. Pickle must not restore stale pre-replacement data.
- How explicit JSON nulls in unknown fields survive a `to_dict()` contract that says “no None.” Omitting absent known optionals differs from recursively stripping unknown nulls.
- Whether equality ignores bot binding, raw whitespace/key order, lazy-rendering locale and subclass state. A local probe found equal wire data bound to different bots compares unequal in current 3.x; D84's “same class + data (3.x)” is not a complete compatibility description.
- Which objects are hashable. Frozen attributes can contain files, lazy values and mutable subclass state. A stable hash cannot depend on locale, mutable raw dictionaries, or bot rebinding. Do not promise universal value hashing without a canonical value domain.
- How pickle preserves registered subclasses and user-added state; raw JSON alone cannot preserve arbitrary Python extension state or an `InputFile` stream.

**Acceptance:** a table of wire-origin versus constructed/replaced objects, round trips for each, stable set/dict membership across allowed operations, and no mutation through returned containers.

### R06 — Accepted alias breaks still require exact behavior and migration rules

**Accepted breaking changes with incomplete specification; P1.** The owner accepts the new alias behavior. The report therefore does not require pydantic parity. Nevertheless [01 §3.7](01-models.md), [16](16-support-policy.md) and the README must expose every change consistently.

| API | Existing local behavior / issue | Required 4.0 statement |
|---|---|---|
| `model_dump_json` | Returns `str`; native `to_json` returns `bytes` | Explicit bytes migration, including text files and frameworks expecting strings. |
| `model_dump_json(by_alias=False)` | Python-name selection is currently meaningful | Document that the flag is ignored, or reject it with an actionable error; do not imply compatibility. |
| `model_extra` | Extras only; often `None` without extras | Whole raw-object alias changes key set, truthiness and `None` behavior. |
| `model_dump` | Common options include Python names, inclusion/exclusion and default handling | Enumerate the supported subset, defaults, return shapes and unsupported options. |
| `model_copy(update=...)` | Not equivalent to a validating reconstruction in general | State whether `replace` validates, how it copies, and whether `deep=` has a supported equivalent. |
| Collection fields / `getUpdates` | Existing code may expect mutable lists | Choose tuple versus copy behavior and list it as a break; the network page specifies a tuple. |
| Unknown model attributes | 3.x extras can be accessed by attribute | State whether `obj.new_field` disappears in favor of `.raw`; `F.new_field` can be affected. |

Also specify missing-versus-explicit-None/default provenance. A shared constructor that delegates to `from_dict` must still accept field values such as datetime, aiogram instances, files and lazy text, not merely wire JSON. The alias implementation is not credibly scoped by “about 50 lines” until that contract exists.

**Acceptance:** executable before/after examples for every supported alias kwarg, and codemod rules that flag semantic changes rather than mechanically renaming every call.

### R07 — Define one permissive policy without erasing every error boundary

**Design gap; P1.** The owner chose a common permissive policy. [01](01-models.md) still promises full eager validation with errors at parse time, whereas [10](10-forward-compatibility.md) falls back to Unknown when no undiscriminated variant validates. Invalid known shapes can therefore become Unknown rather than errors. That may be intentional, but it must be defined uniformly for constructors, dictionaries, JSON, API responses and methods.

Specify known-tag/malformed-payload behavior, missing common fields on Unknown variants, unknown primitive/container union values, conflicting aliases, duplicate JSON keys, integer widths/overflow, bool-as-int, NaN/infinity, UTF-8 errors, cyclic Python containers, and depth limits. “Every union has an Unknown member” is insufficient when a union's wire value can be a scalar or array while `.raw` promises a dict. Leniency does not require accepting invalid JSON or unbounded allocation.

D85 both requires overlay rules for every undiscriminated union and defines a declaration-order fallback without one. Define when fallback is reachable and whether declaration order is stable across regeneration. Unknown values must preserve their wire shape through encoding.

Subclass registration also needs scope and lifecycle: global, dispatcher, bot or decode context; replacement/conflict rules; freeze timing; construction hooks; and error propagation. ABC virtual registration does not inherit implementations or establish static subtype relationships by itself. Prove the generated runtime bases and stubs together.

Pydantic interop requires tests for existing instances, dictionaries, JSON, nullable/nested models, errors and recursive JSON schema. Returning an OpenAPI component directly needs reference/dialect handling. A lazy optional import does not eliminate the need for an explicitly tested compatibility range. [Pydantic custom-type guidance](https://docs.pydantic.dev/latest/concepts/types/#handling-third-party-types).

### R08 — The proposed `.bot` field removal creates an existing name collision

**Confirmed cross-page contradiction; P1.** [11 §1](11-removals.md) removes the `bot_user` alias workaround and says Bot API `bot` becomes a plain field. [01 §3.2](01-models.md) keeps `.bot` as the bound client. Existing [ManagedBotCreated](../../../aiogram/types/managed_bot_created.py) and [ManagedBotUpdated](../../../aiogram/types/managed_bot_updated.py) have a Telegram `User` field named `bot` on the wire. One attribute cannot expose both that user and the client.

**Resolution:** keep an explicit Python alias such as `bot_user`, or move bound-client access to a different reserved namespace consistently. Reserve all framework member names, not just D92's serialization methods. When Telegram adds a collision, generate an alias rather than making codegen permanently fail with no supported escape.

**Acceptance:** construct/decode both managed-bot types; access their user and bound client independently; round-trip the wire key `bot`; retain typed shortcut behavior.

## 5. Routing, runtime and storage

### R09 — One shared dictionary changes failed-candidate isolation

**Locally reproduced semantic difference; P1.** [03 §3](03-routing.md) removes `**kwargs` copies and promises unchanged semantics. D38 correctly describes successful filter results surviving a later `SkipHandler`, but that is not the complete data-scope contract.

Today [HandlerObject.check](../../../aiogram/dispatcher/event/handler.py) receives a candidate-local kwargs dictionary. If filter A adds `{"db": value}` and filter B rejects, [TelegramEventObserver.trigger](../../../aiogram/dispatcher/event/telegram.py) does not commit those results. The next candidate does not see `db`. By contrast, all-successful filters followed by `SkipHandler` do leave their returned data visible. Inner middleware writes before `SkipHandler` also survive within that observer; a probe using the actual `Router.message` observer confirmed this. Nested objects can still be shared because these copies are shallow.

**Resolution:** specify data scopes for update, router, candidate, inner middleware and callable invocation. Preserve the deliberate commit points, for example through a candidate overlay committed on filter success. Alternatively declare an additional intentional break, with concrete examples; do not call a single global dict equivalent. Router-root filter data and sibling traversal need the same analysis.

**Acceptance:** differential cases for partially successful filter chains, false returns, exceptions, `SkipHandler`, sibling routers and nested mutable values. Performance gates must include the cost of whichever semantics are retained.

### R10 — Prefilters need purity and middleware boundaries

**Design gap; P1.** Skipping earlier filters when a later known filter rejects is already an accepted documented break in [03](03-routing.md). That does not prove every proposed rejection is sound. A cached key computed from the original event may disagree with an event substituted by outer middleware or a registered subclass property. Compiling magic-filter's operation tuples also depends on its internal representation while D70 permits uncapped future versions.

Flattening router candidates cannot discard router entry/exit semantics. Outer middleware may short-circuit, transform data/events, call its continuation twice, or surround all descendants. An empty or unmatched router can still have observable middleware behavior. The state index must preserve wildcard/general handlers and DFS precedence; “go straight to the active scene” is too strong without those rules.

**Resolution:** define a supported pure expression subset, fallback for unsupported operations/subclasses, and the point at which routing keys are valid. Preserve router scope frames in the compiled plan. Compile DI/filter plans at dispatcher freeze where router reuse needs dispatcher-specific configuration; registration alone may occur before a router belongs to any dispatcher.

**Acceptance:** optimized and reference executions agree on outcome and allowed trace differences for replaced events, custom properties, `.func`, `.as_`, OR/negation, middleware re-entry, nested routers, state wildcard and exception paths. Only the explicitly documented filter-skipping differences belong in the allowlist.

### R11 — Freeze is a shared lifetime, not a boolean on one Runner

**Design gap and inaccurate safety claim; P1.** D19 thaws after stop, D56 permits routers shared across dispatchers, and [07](07-free-threading.md) shares one dispatcher across multiple runners. If runner A stops while B is active, the shared graph cannot become mutable. A shared router may also remain in use by another dispatcher. `MappingProxyType` prevents writes through a mapping view; it does not freeze contained filters, flags, middleware instances, storage objects or referenced user resources.

**Resolution:** use a documented graph/dispatcher freeze ownership protocol, with concurrent startup and failed startup rollback. Either maintain active-use leases for shared objects or publish immutable configuration snapshots with clearly limited mutation semantics. Treat user middleware/filter/DI providers as shared application objects that must be safe for the chosen execution mode; do not claim the frozen table makes them thread-safe.

Specify direct `dp.feed_update()` behavior before startup and after shutdown. The test toolkit and existing custom integrations use it; a table built only in `emit_startup` leaves that route undefined. Explicitly scope `dp.stop_polling()` to the wrapper-created runner without introducing ambiguous cross-loop dispatcher state.

Also clarify whether “one Runner per loop” means one per dispatcher/loop pair or a process-wide restriction. Two independent applications can legitimately share a loop; a global singleton needs stronger justification than keeping loop-bound state together.

**Acceptance:** two runners share a dispatcher; two dispatchers share a router; stopping one never unlocks a graph still in use; direct feeding has documented initialization semantics.

### R12 — Runner needs admission and lifecycle state machines

**Design gap; P1.** [12 §3](12-runtime.md) has one `feed()` that schedules tasks according to `handle_as_tasks`, applies limits, and returns an inline reply. A scheduled update does not yet have its reply. The protocol also has no explicit processing completion/result for custom sources, despite mentioning Redis Streams and Kafka.

Define an internal distinction between admission, scheduled processing, completion and reply delivery. It can remain a small API, but each source must know what awaiting `feed` guarantees. A semaphore around handler execution alone does not bound queued tasks or retained request bodies. Admission needs a queue/body budget and overload behavior.

The runtime state machine should cover:

- start, startup hooks, initial bot hooks, source activation, stopping, draining and closed;
- add/remove of the same bot concurrently; duplicate token identities; failed `bot_added`; source failure after partial startup;
- session ownership for a shared session, and removal of one bot while another still uses it;
- who owns and closes shared FSM storage when one runner stops;
- sources attached before/after start, and whether one bot may belong to multiple sources;
- cancellation during every hook and shutdown deadline, including user `CancelledError` handling;
- one process-level signal owner in the main thread, with worker-loop runners configured accordingly.

[07](07-free-threading.md) also incorrectly says asyncio is thread-safe since 3.14. Per-thread loops are supported, but most asyncio objects are not thread-safe; signals belong to the main thread. [Python asyncio documentation](https://docs.python.org/3/library/asyncio-dev.html#concurrency-and-multithreading).

For single-bot sharding, define one ingress poller and bounded cross-loop handoff, not N competing pollers. Shard by the configured isolation key where ordering matters; `chat_id % N` has no answer for updates without a chat and does not describe every FSM strategy.

### R13 — Document best-effort delivery as best effort

**Owner-selected policy with incomplete mechanics; P1.** The owner chose existing best-effort semantics. The phrase “nothing gets processed twice” in D22 is consequently too strong. [12 §5](12-runtime.md) commits the polling offset before waiting for in-flight tasks. A crash or deadline cancellation after that point can lose admitted but unfinished work; a failed/uncertain commit can leave replay possible. Telegram acknowledges updates when a later offset is requested, not when handlers finish. [Telegram polling contract](https://core.telegram.org/bots/api#getupdates).

Use distinct names for highest received, admitted and confirmed IDs. State what the removal commit confirms and what happens when the commit request fails. Its `limit=1` response may contain a newly received update: define whether that value is dispatched or left unconfirmed for later polling. No exactly-once claim should be attached to this sequence.

Forward compatibility needs additional edge cases:

- A syntactically valid element with an integer ID but invalid body can become a poison-update shell. Malformed batch JSON or an element without a valid ID cannot always be isolated or safely advanced past.
- Auth failure, body-limit failure, overload and an application bug are different webhook cases. Define their statuses and observability.
- Delivering both `unknown_update` and `errors` needs a deterministic order and a rule for a failure in either observer. Avoid double completion/acknowledgement.
- Define precedence between Bot and Dispatcher `DecodePolicy`, and strict-mode behavior across polling and webhook; “always advance” and “strict raises” are not a complete combined contract.
- Auto-derived `allowed_updates` subscribes only to known observers. An `unknown_update` handler cannot receive future types that Telegram was instructed not to deliver. Document explicit raw subscription settings and their limits. [Telegram subscription parameters](https://core.telegram.org/bots/api#getupdates).

The goal “no upstream addition ever fails a successful API call” also exceeds Layer 2, which deliberately raises `TelegramDecodeError`. Promise recoverable raw data and continued delivery where structurally possible instead.

### R14 — Default event isolation needs a cancellation-safe handoff algorithm

**Design gap; P1.** [04 §3](04-fsm.md) sketches a cross-loop queue and `call_soon_threadsafe(fut.set_result, None)`. A waiter can be cancelled after selection but before the scheduled callback runs. Merely noticing previously cancelled futures does not transfer ownership safely in that interval. A stopped/closed target loop adds another failure mode.

Specify queued, granted, acquired, cancelled and released states; which side owns handoff after each transition; entry pruning while holders/waiters still reference it; and fairness/starvation expectations. Do not block an event-loop thread on a lock whose holder may need that loop to progress. Cover recursively feeding the same FSM key and callbacks that await a later update for the same key: default isolation can deadlock such application patterns.

`MemoryStorage` shard locks protect its map operations, not arbitrary nested Python values returned by shallow copies or direct `storage.storage[key]` access. Keeping that escape hatch means thread safety has a documented boundary. Full scene history snapshots also need a decision about nested-value aliasing.

Finally, atomic merge does not make application read/modify/write atomic. Two callers can both read `n=0` and each atomically write `n=1`. Do not use an increment stress test as evidence that `update_data` alone solves arbitrary lost updates; require isolation or a transactional mutation API for that operation.

**Acceptance:** adversarial cancellation around every handoff, closed-loop waiters, pruning/recreation under contention, explicit nested-data behavior, and separate tests for atomic merge versus serialized read/modify/write.

### R15 — Redis migration is not just a Lua script

**Design gaps with upstream constraints; P1.** [04 §6](04-fsm.md) promises unchanged legacy layout, configurable JSON hooks, atomic one-RTT updates, dual-read migration that deletes old keys, and reversible migration. These properties need additional restrictions:

1. A Lua read/decode/merge/encode script cannot execute arbitrary Python `json_loads`/`json_dumps` hooks. Define the supported server-side codec and a transactional client-side fallback; the latter may require additional RTTs.
2. Round-trip numeric precision, empty arrays versus objects, nested nulls and custom encodings must be verified for the chosen Lua JSON implementation. Atomicity alone does not establish data fidelity.
3. Independent state/data TTLs cannot generally be collapsed into one hash TTL and restored exactly later without extra metadata. Specify min/max/explicit TTL policy, expired halves, persistent keys and rollback lossiness.
4. Legacy keys lack a guaranteed common Redis Cluster hash tag. Multi-key migration and lock+read scripts require all relevant keys in one slot. Preserve legacy standalone operation or define a cluster-aware strategy explicitly. [Redis multi-key constraints](https://redis.io/docs/latest/develop/reference/errors/common/crossslot/).
5. Deleting old keys during lazy migration is unsafe for a rolling deployment where 3.x workers can recreate them. Define migration quiescence/ownership, or a real mixed-version protocol; idempotence is not protection against concurrent legacy writers.
6. `KeyBuilder` currently offers forward construction, not parsing. A bulk SCAN migrator cannot infer arbitrary custom key formats or distinguish state/data keys without an explicit discovery strategy.
7. Multi-bot defaults need attention: current `DefaultKeyBuilder(with_bot_id=False)` can intentionally share keys. Runtime multi-bot convenience must not accidentally suggest isolated storage by default.

The Mongo equivalent needs a return-value contract, not just `$set`: define whether concurrent `update_data` returns a post-update snapshot atomically, and handle arbitrary dictionary keys that conflict with dotted update paths. Scene transitions that update both state and data need their own atomicity statement.

**Acceptance:** migration with independent TTLs, mixed-version writers, interruption, custom key builders, configured codecs and supported cluster modes. Mark unsupported combinations clearly instead of calling all migrations transparent.

### R16 — Typed FSM data is a new validation subsystem

**Scope and semantic gap; P2.** [04 §7](04-fsm.md) and [11 §4](11-removals.md) replace pydantic with converters covering unions, defaults, containers, nested models, dataclasses, dates, Decimal, UUID and optional third-party adapters. This is valuable, but substantially more than a small flat converter table. `dataclass_transform` informs type checkers; it does not implement that runtime behavior.

Resolve default copying (`tags: list[str] = []`), frozen nested containers, coercion, omitted-versus-default fields, adapter precedence, recursive types, serialization/version migration, and actionable field-path errors. `update_data(OrderForm(item_id=5))` needs an explicit rule for whether the default `qty=1` overwrites an existing quantity. A full model and a partial patch are different inputs.

The advertised typed `Scene.data` return also needs a practical typing mechanism, not only a runtime class attribute. Demonstrate mypy/IDE inference for wizard methods and adapters. Keep the existing dict path as a first-class compatibility baseline.

**Acceptance:** an independent converter contract suite, schema evolution examples, mutable-default isolation, and typed examples for every advertised adapter. Retain this feature in 4.0, but estimate and review it as its own subsystem.

### R17 — Depends, error bubbling and teardown need one owner

**Confirmed cross-section ambiguity; P1.** [03 D50](03-routing.md) routes dependency teardown errors to `runtime_errors`, while its Depends section re-raises the first teardown error from `feed_update` after success. D49's `ErrorPhase` omits dependency resolution and teardown even though tracing includes TEARDOWN. The same failure could be reported twice or to the wrong observer.

Also decide what providers see when a handler exception is handled by an error observer: does a transaction provider receive the original exception and roll back, or see a successful outer result and commit? “Throw the update exception into every generator” does not define error suppression, replacement, sync-generator `throw`, cancellation or multiple teardown failures. Use context-manager semantics and an explicit scope object, rather than estimating this as a 100-line resolver.

The provider-only cache key is ambiguous if a dependency consumes router/candidate-specific data and an earlier candidate has already resolved it. Define which inputs are stable within a scope, whether cache identity includes parameters, and what happens when middleware invokes downstream work more than once or concurrently. Resolver precedence, multiple matching markers, overrides and cycles must be checked after final dispatcher configuration.

Error bubbling needs a policy for an error handler that itself fails and attribution before a handler matches. Decode failures need a router path even though no event router may yet be selected. Teardown should complete before a source treats processing as finished.

**Acceptance:** tests for handled/unhandled handler errors, provider failure during matching, rollback/commit choice, cancellation, multiple cleanup errors and no double reporting. D31's kwargs API remains compatible; its “only mechanism” wording should acknowledge the additional resolver mechanism selected by D32.

## 6. Client, utilities and observability

### R18 — Serialization must account for files, defaults and extension hooks

**Confirmed incomplete contract; P1.** [05](05-network.md) correctly has `JsonBody | Multipart`, but its webhook section and [11 §6](11-removals.md) imply replacing replies universally with JSON. A handler can return a method containing `InputFile`. Preserve multipart inline replies or explicitly send such methods through the normal client path, with tracked completion and error behavior. Telegram supports multipart webhook replies; they provide no result confirmation. [Telegram webhook reply contract](https://core.telegram.org/bots/api#making-requests-when-getting-updates).

Likewise `TelegramMethod.to_json()` cannot always produce a self-contained request: files, unresolved `Default` and lazy locale text require context. Define whether this API serializes a model representation, a ready request, or raises for unresolved values. [06](06-utils.md) calls `deserialize_telegram_object` a thin `to_dict` wrapper, but the existing [function](../../../aiogram/utils/serialization.py) also resolves defaults, optionally inserts the method name and extracts files. Those behaviors cannot simply disappear under an “API kept” claim.

The session compatibility branch must cover overridden `check_response` as well as `prepare_value`, custom codecs, raw methods/`returns`, and streaming errors. Explicitly specify bytes versus str for JSON hooks: current hooks commonly produce str, while native serializers return bytes. A fallback built on old model dumping is not defined once the model layer changes.

`DefaultBotProperties` converted once per bot also needs a mutation/update contract. If public Python defaults change later, either rebuild the Rust snapshot or make that change explicitly unsupported. Test fallback behavior rather than only checking method identity.

### R19 — Retry/rate-limit order changes behavior

**Design gap; P2.** [05 D43–D44](05-network.md) uses `get*` as a proxy for read-only methods. `getUpdates` also acknowledges prior updates through its offset; name prefixes are not a sufficient retry-safety model, especially for raw calls and custom API servers. Prefer explicit generated metadata plus user overrides. Do not present “429 always safe” as a proven universal guarantee for every server and raw method; distinguish known rejection from ambiguous transport failure.

A rate limiter outside Retry charges one logical call; a limiter inside Retry can charge every network attempt. The example “before RetryMiddleware” needs an explicit ordering convention and attempt model. Define token reservation/refund on cancellation, deadline composition, backoff jitter, `max_wait` per attempt versus total elapsed time, shared-session per-bot keys and bucket eviction. A per-loop limit is not a global multi-loop/process limit.

Files may be non-replayable streams. Reusing a method object does not rewind an arbitrary `InputFile.read()` implementation. Lazy text may also render differently between attempts unless the request is snapshotted. Make retry eligibility depend on replayability as well as method policy.

**Acceptance:** retry attempts respect limits, cancellation releases pending reservations, raw methods default to a documented policy, and a consumed non-replayable upload is never silently retried.

### R20 — Album middleware needs an ingress/buffering design

**Cross-layer conflict; P1.** [06 D59](06-utils.md) buffers only for selected handlers and holds the FSM lock only during dispatch. But [04 D27](04-fsm.md) acquires isolation and eagerly loads state before routing, while per-handler middleware runs after matching. An ordinary inner middleware cannot buffer before a lock already taken by its outer middleware. It also cannot know all future candidate/flag choices before matching without a separate selection step.

Specify album assembly as a distinct ingress/pre-dispatch stage or define a two-stage matching protocol. State whose update context, dependency scope, trace, reply and exception owns the eventual combined call. Define behavior for late parts after the window, duplicate updates, multiple matching handlers, shutdown flush/drop, removal of a bot, and memory/concurrency budgets. “Calls the handler once” can only mean once per aggregation window, not necessarily once per Telegram album.

**Acceptance:** interleaved albums and ordinary messages for the same key preserve the selected ordering policy; buffering does not hold isolation; no part leaks an untracked task/scope; shutdown and overload have explicit outcomes.

### R21 — Lazy text requires atomic text/entities rendering

**Design gap; P2.** Core support for a lazy-render protocol is justified. Absorbing every engine is a product/maintenance choice rather than a technical consequence of removing pydantic. The owner wants the feature set retained, so assign it independent maintenance and acceptance work.

[06 D61](06-utils.md) renders both text and entity offsets at encode time, while [01](01-models.md) describes only accepting a lazy object in a display-text field. Specify how one render replaces the sibling `entities` field and interacts with explicit entities or `parse_mode`, rather than calling an ordinary string conversion. Render once per request snapshot so locale changes and retries cannot mismatch text and offsets.

Define behavior outside a handler, default-engine selection across multiple runners, engine resource startup/shutdown, gettext versus Fluent key semantics, missing translations, formatting errors and return types in stubs. Storing an arbitrary Python lazy value unchanged is not proof of immutability or thread safety. Hash/pickle and `.raw` semantics from R05 must include these values.

**Acceptance:** concurrently encode one keyboard/formatting tree under two locales, with non-BMP characters and nested entities; outputs remain independent and retries preserve the chosen request snapshot.

### R22 — Default token redaction is ineffective as specified

**Locally reproduced and verified; P1.** [15 §5](15-observability.md) attaches a filter only to the `aiogram` logger. Python does not apply ancestor logger filters to records emitted by descendant loggers. A local stdlib probe confirmed that a record from `aiogram.child` would bypass that arrangement. [Python logging rules](https://docs.python.org/3/library/logging.html#filter-objects).

The same section preserves an unsanitized original exception as `__cause__`. A redacted outer message does not redact a normal formatted traceback: the chained cause is printed. A second local probe confirmed this. A filter editing message/args also does not automatically sanitize formatter-generated exception text.

**Resolution:** sanitize framework-generated structured records and exception representations at their actual emission/formatting boundaries, with tests covering child loggers and chained exceptions. Define the coverage of the provided logging setup versus arbitrary user handlers/formatters. A library cannot guarantee sanitation of external reverse-proxy logs. ASGI hosting needs an explicit access-log configuration, not merely a broad “on by default” statement.

**Acceptance:** fabricated tokens are absent from framework log messages, arguments, structured URL fields, exception chains, traceback text and configured aiohttp/ASGI access logs. Redaction itself must not raise or destroy useful error attribution.

### R23 — Tracing needs bounded behavior and measured overhead

**Design gap; P2.** [03](03-routing.md) promises tracer exceptions never change routing; [15](15-observability.md) uses arbitrary synchronous context managers. A tracer's `__exit__` could suppress an application exception, replace it, or fail. Multiple tracers need balanced exit handling and a defined result/status interface. `ContextManager[Span | None]` alone does not specify how attributes are updated safely.

“One enter/exit per stage” is not the cost with multiple tracers. “Zero cost without tracing” should mean no hot-path instrumentation work in the compiled no-tracer plan, measured against the same plan without hook support. Exporter behavior and user tracers can still block.

Bound unknown tag/method warnings and metric labels: arbitrary raw method names, unknown update types and runtime bot IDs can create unbounded maps even when user/chat IDs are excluded. Clarify whether handler/router labels are stable names, object reprs or user-supplied strings. Keep IDs appropriate for diagnostic logs out of high-cardinality metrics by default.

Also provide update logging context for direct `dp.feed_update`, not only Runner-driven calls, or document the reduced context on that path. Avoid duplicate emission when the legacy logger “alias” is kept.

**Acceptance:** tracer failures and truthy `__exit__` never suppress application failures, labels have bounds, no-tracer overhead is measured, and direct feed has a defined observability contract.

## 7. Generation, release, migration and documentation

### R24 — Commit enough provenance to reproduce the generator

**Design gap; P1.** The two-adapter IR in [02](02-butcher.md) is a good boundary. However, sources are downloaded into an uncommitted cache, while CI must regenerate identical output. Committed derived IR can reproduce emission; it cannot by itself reproduce or audit source extraction. These are different checks.

**Resolution:** separate offline `emit/check` from online source-refresh auditing. Record exact source URL, fetch time, source digest, parser/tool versions, overlay/ledger versions and whether generation was HTML-only. Retain source snapshots or an immutable retrievable source bundle with a documented provenance/license policy. Do not make ordinary CI depend on a mutable live page or staging availability.

“Unchanged entity” needs a semantic definition including referenced types, parameter defaults, union order and constraints, not only a matching field set. A same-version disagreement should not automatically establish that the schema is correct: preserve both facts and require an explicit resolution for structural discrepancies. Prior schema facts can be stale even when a type's own names have not changed.

D18's merged input/output class may remain the public API, but the IR should retain direction-specific requiredness, constants and writable fields. Otherwise merging weakens the information needed for diagnostics, fake response generation and request encoding. Under the chosen permissive policy, this metadata can inform diagnostics rather than enforcing stricter outbound rejection.

Not every new field should automatically become a content kind or event type. `send_copy`, event-context extraction, lazy display fields, fake permissions and raw method retry metadata need an explicit inventory of semantic overlays. Some facts cannot be inferred from field names or an OpenAPI schema. The strict overlay-key design is useful, but the listed overlay currently omits several later features' metadata.

**Acceptance:** regenerate offline from a clean checkout; replay a historical HTML/schema disagreement; demonstrate a new union, colliding name, input/output mismatch and unsupported `send_copy` content without silently misgenerating behavior.

### R25 — Build and platform policies need empirical support tiers

**Evidence qualification and release gap; P2.** A single distribution is a sensible initial choice: it avoids Python/core version skew. A single Rust crate is also a reasonable prototype baseline. The community measurements do not prove one layout is universally best for this different lazy architecture, contributor machine or CI runner.

D102's placement rules are compiler/toolchain-sensitive optimization hypotheses. Rust's own documentation describes collection and partitioning, including different behavior for generic dependency code; it is not a stable user-language guarantee that every relevant generic always lands according to the stated simplified rule. [Rust compiler guide](https://rustc-dev-guide.rust-lang.org/backend/monomorph.html).

Measure cold builds, incremental helper edits, generated-type edits, memory and binary size on actual CI hardware. A “largest unit > 2× median” threshold can fail a healthy inherently skewed build. Calibrate it against expected unit structure and wall-clock regressions. `-Ztime-passes` needs an explicitly separate nightly toolchain; do not quietly change the compiler being compared. The rustls/aarch64 requirement copied into [08](08-build-release.md) is not established as relevant when this design deliberately excludes Rust networking.

Define guaranteed versus best-effort platforms, what missing wheels block a release, and the fallback message for unsupported systems. “If cheap” is not a publishable support policy. Test the sdist offline build, packaged stubs/data, and installed wheels. Pin CI toolchain separately from the documented MSRV; measure before promising latest-stable-minus-two as an ongoing support burden.

PEP 803's Final/3.15 status is confirmed. It also describes combined `abi3.abi3t` compatibility; future matrix reduction should be measured against the actual API used, not assumed to be a drop-in switch. [PEP 803](https://peps.python.org/pep-0803/).

Pure Python dependencies are not automatically safe for concurrent use. Exercise enabled extras under free-threaded jobs and publish the supported combinations. Lower bounds only is defensible, but private magic-filter integration and optional pydantic hooks require scheduled compatibility checks plus a rapid response policy when upstream changes break released installs.

### R26 — Keep differential testing, add explicit difference manifests

**Validation gap; P2.** The poison controls and installed-wheel typing checks in [08](08-build-release.md), [13](13-aiogram-rust-review.md) and [14](14-testing.md) are strong choices. Keep them. But routing and serialization intentionally change in 4.0; requiring unconditional 3.x parity contradicts those decisions.

Classify each corpus case as invariant, approved difference or newly supported behavior. An approved difference should have a narrow semantic assertion and decision ID, not a broad snapshot exclusion. Cover constructors, `replace`, aliases, defaults, Unknown paths, custom sessions and wrappers, not just happy-path JSON from Telegram.

Typed fake interception does not exercise encoding/decoding, and the fake is not an independent oracle for all Telegram semantics. Deriving both expected and actual values from the same IR can miss an incorrect mapping. Retain hand-curated wire fixtures and recorded traces, with redaction and provenance. Mark modeled versus synthesized fake methods visibly so a successful synthetic result cannot be mistaken for faithful server behavior.

The fake's identity promise must follow R02's ownership decision. Its single-loop limitation should not prevent separate production multi-loop tests. Test clocks must cover cancellation, rate limits, aggregation and deadlines consistently.

The “100% coverage” goal is not a substitute for correctness, and excluding generated Rust from a percentage threshold does not justify excluding it from property/differential/fuzz execution. Add malformed-data fuzzing, bounded-memory cases, GC/lifetime tests, and fault injection at startup/shutdown boundaries.

**Acceptance:** each harness detects deliberate corruption, has reviewed expected differences, and exercises the real public entry paths rather than only internal functions.

### R27 — Do not ship all proposed quick wins as compatibility-preserving bugfixes

**One reproduced defect plus several design risks; P1.** [09](09-3x-quick-wins.md) is useful, but the label “small focused PR” needs case-by-case evidence.

| Item | Review |
|---|---|
| #2 shallow keyboard copies | **Incorrect premise.** `InlineKeyboardButton` inherits `MutableTelegramObject`. A probe confirmed that its text can be changed and that current `export()` isolates that change through deepcopy. Preserve exported-object isolation in 3.x. Optimize internal row operations only after deciding which existing aliasing behavior is contractual. |
| #6 root-only bot binding | This changes ownership/lifetime semantics, not just a post-init cost. R02 applies even before Rust. Benchmark benefits only after a compatibility-preserving design exists. |
| #4 pruning plus #12 returning bare locks | Pruning requires accounting for holders and waiters. Returning an uninstrumented lock bypasses a wrapper's release bookkeeping unless the lock itself carries it. `setdefault` fixes only one creation race. |
| #1 inline MagicFilter | `.func(blocking_fn)` can run arbitrary sync work. The behavior change is acknowledged, but a fragment alone does not make it harmless; provide the thread-mode escape where applicable. |
| #10 JSON webhook replies | Retain upload behavior; R18 applies to 3.x too. |
| #15 replacing sentinels with `object()` | Check repr, deepcopy and pickle singleton behavior. A plain `object()` is not automatically a semantic replacement for `unittest.mock.sentinel`. |
| #18 Lua/pipeline `update_data` | Pipeline alone is not an atomic read/merge/write operation; a Lua implementation has codec concerns from R15. |
| #21 poison-update handling | Valuable, but unconditional advance means deliberate data loss. Apply the chosen best-effort policy only after decoding/error/status boundaries are specified. |
| #5 deferred rebuild | Verify every generated forward reference and first-use concurrency, not only import timing. |
| #14 cached fake Bot | Verify defaults, session ownership and cross-loop use; removing the need for a fake Bot is a cleaner possible boundary than a process-global client cache. |

**Recommendation:** start with independently verified fixes such as read-without-record-creation, and measured filter dispatch fixes with a compatibility escape. Track each patch's actual measured baseline. Do not count speculative root-only binding or changed export semantics as already available “optimized 3.x.”

### R28 — Migration/support promises need a realistic enforcement model

**Confirmed inconsistencies and feasibility gaps; P2.** The owner accepts the removals and alias changes. That resolves the product choice; it does not validate every claimed automatic migration.

- [16](16-support-policy.md) promises a checker for every incompatibility, including blocking I/O in sync filters and behavioral reliance. [18](18-docs-migration.md) correctly says several such behaviors cannot be found statically. Distinguish definite findings, heuristic findings and manual checklist items; give each a confidence level and suppression mechanism.
- A mutation-to-`replace` codemod must reassign the result and account for aliases. `obj.x = y` cannot safely become a discarded `obj.replace(x=y)`. Arbitrary class handlers, markdown/escaping changes, imported aliases, receiver inference and pydantic-specific dumping also require conservative fallbacks.
- Last-3.x warnings cannot both precede GA and be limited to the literal last 3.x minor when Bot API bumps continue for 12 months after GA. Name a migration-baseline 3.x release, then keep those warnings through subsequent maintenance releases.
- Explain the major-release reset as an exception to D71's rolling deprecation rule; otherwise newly announced 3.x removals can violate the advertised 12-month window.
- Earliest removal depends on both elapsed time and releases. CI should require an explicit due-removal decision, not assume a fixed version proves the time condition. [02](02-butcher.md) still says plain `DeprecationWarning`, whereas D72 specifies the visible aiogram subclass.
- Removing APIs and Python 3.11 in minors may be the intended policy, but it must be prominent enough for applications that assume `<5` means no further breaks. Support periods and warnings must be operationally supportable across both generators.
- Installing a `default` warning filter at import must not override an application's explicit `-W error` or ignore policy. Test ordering rather than assuming category-specific flags win.
- The migration CLI ships with v4. Document a separate invocation such as an isolated tool environment against a 3.x source tree; “works before upgrading” must not require replacing the running application's dependency first.

“No real usage seen” in [11](11-removals.md) is not evidence of no external usage. The accepted removal rationale is simplification with a migration cost, not proven absence of users. Keep the agreed removals and give affected users honest examples and limits.

### R29 — Prove documentation builds without importing the extension

**Verified tooling distinction; P2.** [18 D79](18-docs-migration.md) treats Sphinx autodoc and static stub analysis as interchangeable. Standard autodoc imports documented modules. [Sphinx autodoc documentation](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html).

Sphinx AutoAPI is a viable static path, but its documented default prefers `.py` over `.pyi`. In this design `.py` files are thin re-exports while the useful type documentation lives in stubs. Configure stub precedence deliberately. [AutoAPI file-pattern configuration](https://sphinx-autoapi.readthedocs.io/en/latest/reference/config.html).

Framework autodoc also matters: importing Python modules can import `aiogram.__init__` and `_core` transitively. A docs dependency group does not itself prevent project installation from building the extension. Choose a fully static path, targeted safe mocks, or a wheel-backed framework-reference build and state which guarantee actually holds.

**Acceptance:** clean docs build with no compiled extension and no Rust toolchain, using representative recursive types, helper fragments, aliases, generated defaults, inherited members and framework modules. Test import-free installation/build commands explicitly. Keep D80's structure, narrative-only translation and executable examples.

### R30 — CLI, plugins and command synchronization need observable contracts

**Design gap; P2.** [17](17-cli.md) is a reasonable standard-library CLI scope. However, entry-point compatibility is not enough to make old click plugins work under argparse. Define argument forwarding, help, exit codes, plugin name collisions, loading failures, and when click is imported. Existing plugins may depend on `aiogram-cli` or `aiogram<4`; a runtime adapter cannot repair incompatible package metadata. The final legacy release also needs a plan for two distributions owning the same console script during upgrade/uninstall.

`run webhook` needs an explicit multi-bot URL/token/secret mapping; repeating tokens is not enough. Define webhook setup failure/rollback, authentication before creating on-demand bots, shutdown cleanup and reload behavior.

For D60 command synchronization, `delete_missing=True` needs a known inventory of scopes/languages previously managed by the application. The desired set alone does not identify which remote scopes to delete. Specify conflicting descriptions across routers, order, deduplication, localization and why `CommandStart` is excluded even if a user wants it advertised.

`info` can report installed packages and capabilities; installation metadata does not necessarily reveal which extras a user originally requested. Label this output accordingly. Coordinate the separate `aiogram.fsm.migrate` entry point with the main migration CLI so documentation and error codes are consistent.

**Acceptance:** CLI smoke tests for factories/coroutines, startup failures, reload, multi-bot webhook configuration and both plugin formats; deterministic dry-run plans for command and storage migration.

## 8. Smaller consistency corrections

These do not all need independent architecture decisions, but they should be tracked alongside the larger findings.

| Location | Correction to make when the owner updates the source pages |
|---|---|
| README D4 versus 02 §2 | Rust types are generated from the resolved IR; OpenAPI is not always available or the active source. |
| README “small, documented breaks” | The listed changes amount to a substantial framework migration. Set expectations accordingly without changing the accepted scope. |
| README final roadmap phase | Shipping `4.0.0a1` is an alpha milestone, not completion of the GA release plan or start of the 3.x support countdown. |
| 03 §3 | Remove `REJECTED` from the unchanged-semantics list if 11 removes it. |
| 03 D31 versus D32 | Explain kwargs data lookup and explicit dependency resolution as cooperating mechanisms, not “only one” mechanism plus an unacknowledged second one. |
| 01 and 05 decode descriptions | “No intermediate tree” is useful; “one pass” is inaccurate where a raw value is skipped to locate a slice and then decoded, or a union tag is scanned first. Benchmark total lexing work. |
| 01 versus 08 | Clarify Rust data structs, Python views and the claim that “there are no wrapper types.” The memory/lifetime diagram should be normative. |
| 08 constructor advice versus 01 signatures | `(**kwargs)` implementation and generated keyword-only public signatures can coexist, but real `inspect.signature` must be tested for `Default(...)` and other nonliteral defaults. |
| 03 typed DI example | `total=False` on a TypedDict subclass does not make inherited required keys optional. Model `state`, `raw_state`, `handler` and event-specific keys according to their actual availability. |
| 10 test policy | Use strict mode for known-schema corpus tests; explicit lenient-mode tests are still required for the forward-compatibility feature itself. |
| 13 B17 | Put accepted datetime/timezone/rounding and timeout behavior in the normative API sections; a borrowed-lessons row is not sufficient specification. |
| 08 “zero runtime dependencies” | The Rust component may add no Python runtime package dependencies; distinguish that from platform/system library and packaging requirements. |
| README decision index | Include all extras consistently, including migrate/reload and storage/network extras, or explicitly link to the authoritative complete list. |
| 06 / 11 external package deprecation | Track ownership and release coordination for `aiogram_i18n`/`aiogram-cli`; the core repository cannot accomplish those releases by documentation alone. |

## 9. Proposed implementation sequence, retaining the 4.0 scope

The owner's preferred outcome is a complete 4.0 feature set delivered through smaller parts. The following sequence changes implementation order and gates, not that product scope.

The design choices I would retain are Python-owned routing/FSM/network orchestration; coarse synchronous Rust entry points; a single distribution initially; generated API/stubs with separate hand-written extensions; per-version wheels for the initial release; explicit opt-in testing/observability integrations; and a shared migration registry. None requires accepting the unresolved semantics above.

Two implementation-language choices deserve separate cost validation. A Rust generator can reuse Rust-side type knowledge and toolchains, but it does not improve runtime throughput merely by being written in Rust; compare parser/overlay maintenance and contributor iteration against the existing Python expertise. Similarly, moving tiny convenience helpers into Rust is defensible for one-class ownership, but not every such helper has a performance case. Include helper-edit rebuild time and contributor experience in the spike, rather than treating these choices as consequences of D4.

| Milestone | Reviewable deliverable | Exit gate / dependencies |
|---|---|---|
| A — Contracts and baselines | Resolve R02/R05–R13; record accepted differences; land independently safe 3.x fixes | Behavior oracle and pinned benchmark inputs exist before optimizations. |
| B — Ownership/model spike | Representative wide types, Unknown variants, cache seeding, binding views, GC, subclassing and request encoding | Original numerical gates pass; memory/lifetime/cancellation checks also pass. On failure reopen model-dependent decisions. |
| C — Reproducible generation | Source manifests, IR/overlay/ledger, generated types/methods/stubs, helper workflow | Offline emission is deterministic; historical diffs and naming collisions are covered. |
| D — Client and wire paths | JSON/multipart, raw calls, default resolution, custom sessions, webhook replies, download/upload lifecycle | Differential request/response cases, hook compatibility and cancellation/resource tests pass. |
| E — Routing and runtime | Semantic compiled router, graph freeze leases, Runner/source lifecycle, errors and bounded admission | Routing differences match reviewed decisions; lifecycle fault injection and multi-runner tests pass. |
| F — FSM and scenes | Default isolation, atomic merge contract, typed data, history batching, Redis layouts/migration | Race tests and migration matrices pass; application-level lost-update limits are documented. |
| G — User-facing additions | Depends, i18n/formatting, albums, retry/rate limiting, commands and CLI | Each feature has its own contract tests; depends on stable lifecycle/isolation/encoding boundaries. |
| H — Testing and observability integration | Testing World, trace hooks, OTel, logging/redaction | Production code can be exercised independently of the fake; all redaction and trace-failure tests pass. |
| I — Distribution and migration beta | Wheel/support matrix, installed-wheel typing, sdist, import-free docs, codemod/checker, examples | Fresh-machine installation and 3→4 migration rehearsals pass across supported tiers. |
| J — GA readiness | Complete required feature inventory, migration guide, release notes, published support dates | Alpha/beta feedback resolved; no unresolved P1 contracts; rollback and release ownership documented. |

Some implementation can proceed independently after its input contracts stabilize. Keep a visible dependency graph: binding semantics precede fake identity; runtime scopes precede Depends and albums; codec/default contracts precede lazy formatting and retries; storage migration semantics precede the migration CLI.

Do not put every feature on the three-week model-spike critical path. Conversely, do not count prototypes or alpha publication as fulfilling the complete 4.0 release scope.

## 10. Benchmark and acceptance plan

Retain the existing parse/memory/access/dispatch thresholds unless the owner explicitly changes them before a new measured attempt. The accepted answer is to reconsider the design on failure, not relax a failed threshold afterward.

| Dimension | Required workload |
|---|---|
| Decode | Small text update; realistic nested update; wide sparse Message; large media/entities; Unknown variants; 100-update response envelope; sendMessage response. |
| Access | First and warm scalar/nested/collection reads; real filters; formatting; constructor-seeded wrappers; registered subclass fallback. |
| Memory | Native + Python live allocations/RSS; untouched, typical and fully materialized trees; raw access; retained child from batch; repeated parse/drop/GC. |
| Dispatch | First/middle/last/unmatched; ordinary and compiled filters; router nesting; FSM on/off; error/unknown paths; no tracer and tracing enabled. |
| Scheduling | Event-loop latency during large decode/encode; default isolation contention; bounded queues under overload; single-loop and shared-dispatcher multi-loop. |
| Request building | JSON, multipart, nested files, defaults, raw calls, lazy locale rendering; normal and overridden session hooks. |
| Developer/release cost | Cold/incremental Rust build, clean install, import time/RSS, wheel/binary size, full release duration and low-core CI. |

Store benchmark scripts, payload hashes, commit IDs, toolchain/dependency locks, build flags, hardware details and raw samples. The README's best-of-N historical measurements and the spike's median-of-seven measurements should not be compared as if they were the same estimator. Report distributions and uncertainty; add sustained GC-on tests to the GC-off microbenchmarks. Evaluate on Linux as well as the current macOS measurements.

Do not compare the community port's Windows payloads and this checkout's macOS payloads as though the ratios share a baseline. Do not use an unimplemented 3.x optimization as the measured baseline. Include practical absolute CPU and memory changes so a large ratio on a tiny operation is not mistaken for a large application benefit.

## 11. Verification record

These were small direct probes in the existing checkout, not new repository test files:

| Probe | Observed result | Finding supported |
|---|---|---|
| Assign `InlineKeyboardButton.text`; mutate an exported builder button | Assignment succeeds; current exported copy does not mutate the builder | R27 |
| Bind a decoded child's `.as_()` to another fabricated Bot | Root and nested chat retain their original bot | R02 |
| Compare equal wire updates bound to different Bot objects | Equality is false in current 3.x | R05 |
| Inspect `model_dump_json()` return type | `str` | R06 |
| Inspect `model_extra` with one unknown field | Only the unknown field is included | R06 |
| Dump an extra nested dictionary containing null with `exclude_none=True` | Nested null remains | R05 |
| First candidate's filter returns data, then another filter rejects | Next candidate does not see returned data | R09 |
| Successful filters followed by handler `SkipHandler` | Next candidate sees the filter data | R09 |
| Actual `Router.message` inner middleware writes data then raises `SkipHandler` | Next candidate sees the middleware write | R09 |
| Filter only on a parent logger; emit from its child | Parent filter is bypassed | R22 |
| Redacted outer exception chained from a fabricated secret-bearing cause | Formatted traceback still contains the marker | R22 |

One preliminary middleware probe used a separately constructed observer rather than the router's registered observer; it did not exercise inherited middleware resolution and was discarded. The corrected probe above used `Router.message`. This distinction matters when reproducing the result.

Upstream checks support the specific claims linked beside the findings: PyO3 cache/GC constraints, Python logging and asyncio behavior, Telegram acknowledgement/subscription/reply rules, Redis same-slot constraints, Sphinx/AutoAPI behavior, compiler partitioning documentation and PEP 803 status. They do not validate every dated dependency or community benchmark claim in the source pages.

Artifact checks: all 19 original page hashes matched after writing the report; all local Markdown links resolved; finding IDs R01–R30 were unique and complete; the report had no trailing whitespace. A repository-wide `git diff --check` reported pre-existing trailing whitespace in `dialogue.md`, which was left untouched. Because this report is in an untracked directory, its whitespace was checked directly rather than relying on `git diff` to include it.

## 12. Decisions still needed

The interactive answers settled scope, delivery policy, alias breaks, removals, common permissiveness and the binding spike gate. The remaining questions are concrete implementation decisions, not a request to repeat those answers:

1. **Binding/identity:** adopt independent bound views, per-wrapper binding, or explicit tree mutation? What precisely remains of the cross-parent/testing identity promise?
2. **Raw/value semantics:** fresh versus cached read-only raw data; behavior after replacement; collection types; hashability and pickle for non-wire values?
3. **Permissiveness:** how are malformed known union members, primitive Unknown values, conflicting aliases and invalid JSON distinguished?
4. **Routing:** preserve failed-candidate data isolation? Where can middleware replace events before optimized keys are computed?
5. **Lifecycle:** what does awaiting `runner.feed` guarantee, how is admission bounded, and who owns shared resources and freeze leases?
6. **Errors:** what do dependency generators see after an error handler suppresses an exception, and which observer owns teardown failure?
7. **Storage:** which codecs, TTL mappings, cluster layouts and mixed-version migration scenarios are supported?
8. **Albums/i18n/retries:** where does buffering occur, and when is a complete replayable request snapshot created?
9. **Support/release:** which wheels/extras are release-blocking, which are best-effort, and what are the beta/GA completion criteria beyond alpha publication?

These questions should become explicit decisions or acceptance cases before the relevant implementation is approved. The existing plan supplies a strong direction; these contracts are what would make it executable and reviewable.
