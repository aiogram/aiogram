# 09 — 3.x quick wins (pure Python, ship now)

Independent of v4. Each is a small, focused PR with a `CHANGES/` fragment and tests, **measured against its own
baseline** (D120). Together they become the honest baseline the v4 spike must beat (01 §5). D120 dropped #6 and
#15, reworked #2, and attached compatibility notes to #1, #10, #18 and #21–22.

| # | Change | Where | Measured / expected | Type | Notes |
|---|---|---|---|---|---|
| 1 | Resolve `MagicFilter` inline instead of `asyncio.to_thread` | `dispatcher/event/handler.py:77,85-89` | 43.4 → 0.78 µs per `F` filter; 52-handler worst case 1 900 → 220 µs | bugfix | `.func(blocking_fn)` would now block the loop: the fragment alone doesn't make it harmless, so provide a thread-mode escape (D120); user sync callables keep the thread |
| 2 | `KeyboardBuilder`: fix the O(n²) in `add()`; `export()` uses a per-button `model_copy` (reworked, D120) | `utils/keyboard.py:161,171` | `export()` 63 → 8.7 µs | bugfix (O(n²)) | buttons are `MutableTelegramObject`s in 3.x, so exported-object isolation is kept |
| 3 | `MemoryStorage` read paths use `.get()` | `fsm/storage/memory.py:35,46` | −537 B per stateless user (unbounded growth) | bugfix | |
| 4 | Prune `SimpleEventIsolation` locks + atomic `setdefault` | `fsm/storage/memory.py:82,86` | −332 B per key; fixes duplicate-lock race (13/3000) | bugfix | |
| 5 | Remove import-time `model_rebuild` loop; `defer_build` on `TelegramMethod` | `types/__init__.py:968-971`, `methods/base.py:79` | import 1.4 s → ≈0.3 s *est.* | perf | check that first-use rebuild works for every forward ref |
| ~~6~~ | ~~Bind bot on the root only~~ | `client/context_controller.py:11-25` | — | — | **dropped (D120)**: changes ownership semantics, not just a post-init cost |
| 7 | `Literal["x"]` instead of `Literal[Enum]` for tag fields | generated types (via `.butcher` templates) | removes 80 Python callbacks per update | perf/butcher | use the butcher path (AGENTS.md) |
| 8 | Field discriminator for `RichTextUnion` | `types/rich_text_union.py:70` | removes Python discriminator call | perf/butcher | |
| 9 | JSON request body when no files; `pydantic_core.to_json` default `json_dumps`; `prepare_value` fast path when not overridden | `client/session/aiohttp.py:145-159`, `session/base.py:188-259` | encode 93 → ≈21 µs; ≈−30% CPU per API call | perf | keep subclass behaviour (fast path only for the default `prepare_value`) |
| 10 | Webhook: JSON reply instead of `MultipartWriter` when the method has no files | `webhook/aiohttp_server.py:334-358` | small | perf | keep multipart for methods with files (R18 applies to 3.x too, D120) |
| 11 | Prebuild middleware chains (outer/inner, session middlewares); invalidate on register | `dispatcher/middlewares/manager.py:56`, `client/session/middlewares/manager.py:53-61` | ≈5–8 µs/update *est.*; aiogram_rust measured 18.6 → 13.4 µs for one handler | perf | invalidate with a global topology epoch bumped on any middleware register/unregister and `parent_router` change ([13](13-aiogram-rust-review.md) B15); also cache the per-observer outer chains, which aiogram_rust doesn't |
| 12 | `SimpleEventIsolation.lock` returns the `asyncio.Lock`; `DisabledEventIsolation` a shared `nullcontext()` | `fsm/storage/memory.py:84` | −1.5 / −1.1 µs per update | perf | |
| 13 | Cache `bot.id`; `StateFilter` frozenset; `State.state` computed once | `fsm/middleware.py:46`, `filters/state.py:36`, `fsm/state.py:25-36` | ≈1–2 µs | perf | |
| 14 | `deserialize_telegram_object`: cache the fake bot (no SSL context per call) | `utils/serialization.py:15,56` | 4.5 ms → ≈50 µs | bugfix | |
| ~~15~~ | ~~Replace `unittest.mock.sentinel` imports with `object()`~~ | `types/base.py:2`, `dispatcher/event/bases.py:5` | — | — | **dropped (D120)**: repr, deepcopy and pickle singleton behaviour differ |
| 16 | `CallbackData` prefix fast-fail before split+validate | `filters/callback_data.py:188` | non-matching filter ≈8 → 0.2 µs | perf | |
| 17 | (held back until its fix is released) | — | — | bugfix | |
| 18 | Redis: one-round-trip `update_data` (Lua/pipeline) | `fsm/storage/redis.py`, `storage/base.py:187-189` | −1 RTT per `update_data` | perf | a pipeline alone is not an atomic read/merge/write, and Lua can't run user codec hooks (D120, D113) |
| 19 | `Text.render` returns UTF-16 length, no re-encode per nesting level | `utils/formatting.py:50,95` | ≈20–30% | perf | |
| 20 | `TextDecoration._unparse_entities`: single stack pass | `utils/text_decorations.py:96,111` | O(n²) → O(n) | perf | also the reference implementation for v4 Rust parity |
| 21 | **Per-update isolation in polling**: decode `getUpdates` result as raw list, validate each `Update` separately; on failure log, emit to `errors`, advance offset | `dispatcher/dispatcher.py:222-258` | one unknown union tag currently fails the whole batch and stalls polling forever (reproduced) | bugfix | see [10](10-forward-compatibility.md) §5. Advancing past a poison update is deliberate data loss: apply the best-effort policy (R13) only once decoding/error/status boundaries are specified (D120) |
| 22 | (held back until its fix is released) | — | — | bugfix | |
| 23 | Fallback `Unknown` variant for discriminated unions (callable `Discriminator`) | `.butcher` templates | unknown tags no longer fail validation | feature | larger; optional in 3.x |

Suggested order: **21, 22**, 1, 2, 3+4, 9, 5, then the rest.
