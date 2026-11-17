# 01 — Data models: Rust-native types

## 1. Today (dev-3.x)

- `TelegramObject` (`aiogram/types/base.py:10-20`) = `BotContextController` + `BaseModel` with
  `use_enum_values`, `extra="allow"`, `validate_assignment`, `frozen=True`, `populate_by_name`,
  `arbitrary_types_allowed`, `defer_build=True`. `MutableTelegramObject` (`:23`, 17 files) is `frozen=False`.
  `TelegramMethod` (`aiogram/methods/base.py:79`) has `extra="allow"` and no `defer_build`.
- 429 `TelegramObject` + 236 `TelegramMethod` classes. No field/model validators left (#1978 removed
  `remove_unset`). `DateTime` uses a `PlainSerializer` (`aiogram/types/custom.py:23`). 25 discriminated
  unions; `RichTextUnion` uses a **Python callable** discriminator (`rich_text_union.py:70`); 12 unions are
  undiscriminated (`MaybeInaccessibleMessageUnion`).
- Bot binding: `BotContextController` (`aiogram/client/context_controller.py:11-25`) keeps `PrivateAttr _bot`,
  set in `model_post_init` from `context["bot"]` — **on every one of the 30 objects** of an update.
- `aiogram/types/__init__.py:968-971` calls `model_rebuild` on every entity at import, defeating `defer_build`.

Inbound: polling/API responses → `BaseSession.check_response` (`client/session/base.py:88-102`) →
`Response[T].model_validate_json(..., context={"bot": bot})`. Webhook → `request.json()`
(`webhook/aiohttp_server.py:149,196`) → `Update.model_validate(dict)` (`dispatcher.py:199,478`).
Re-mount for another bot: `model_dump` + `model_validate` (`dispatcher.py:157-165`).

### Measurements

| What | Value |
|---|---|
| `Update.model_validate_json` (2 511 B, 30 models) | 84 µs (`json.loads` alone 15 µs) |
| `json.loads` + `model_validate` (webhook path) | 101 µs |
| Python work inside that (post_init ×30, 80 `Literal[Enum]` lambdas, RichText discriminator) | ≈30 µs (35%) |
| User-like model: with PrivateAttr+post_init / without / also without `extra=allow` | 1.94 / 0.93 / 0.74 µs |
| `getUpdates` 100 updates | 8.9 ms |
| `model_dump()` / `model_dump_json()` | 64 / 70 µs |
| Re-mount round-trip | 179 µs |
| Memory per realistic `Update` | **42.5 KB** (decoded dict 11.9 KB, raw JSON 2.5 KB) |
| `Message` instance | 130 fields, `__dict__` 3 328 B, typically 12 set |
| Plain text message (3 models) | 8.1 KB |
| `import aiogram.types` | 1.46 s (920 ms self-time = rebuild loop; pydantic itself 56 ms) |

## 2. Why not "optimised pydantic" alone

Optimised pydantic (3.x track: drop rebuild loop, plain `Literal["x"]`, field
discriminators; root-only binding dropped by D120) gives ≈1.7× parse and ≈5× import *est.* with no break — it is in [09](09-3x-quick-wins.md)
and becomes the **baseline the spike must beat**. It cannot fix memory: pydantic materialises every nested
object as a Python object with a full `__dict__`. Rust-native types target ≈3–5× more parse speed and
≈5–10× less memory *est.* (D4).

Rejected alternatives: msgspec-style structs (no bot context, C not Rust, same compat loss); "Rust decode →
pydantic `model_construct`" (pays both conversions — the research flags this as a likely net loss).

## 3. Design

### 3.1 Storage: Rust data tree, Python views on demand

```
Update view (pyclass, frozen) ── Arc<UpdateData> + raw: Arc<[u8]> (this update's own bytes) + bot: Option<Py<Bot>>
   .message ─▶ sparse cache slot (built on first access, published by atomic set → identity stable within the view)
                 └─ Message view (pyclass) ── Arc<MessageData> (shared with parent tree) + the parent view's bot
```

- Decoding does a **full, eager validation into Rust structs** (jiter, no Python objects). Only *Python wrapper
  objects* are lazy. One permissive policy applies everywhere (R07, D107): a malformed member of a *decoded* union
  becomes `Unknown…` with `.decode_error`; failures outside any union are a per-update `UpdateDecodeError`
  (10 Layer 2), or `ValueError` from `from_json` / `from_dict`.
- The decoder is **table-driven and generated**: per type a field table + `Partial` struct with `set_once` /
  `finish`, not `#[derive(Deserialize)]`, and no `#[serde(flatten)]`. aiogram_rust measured 1.35× faster parsing
  and 196k fewer macro lines (13 B1). Nesting depth is bounded (128) and guarded with `stacker` by re-entry, with each body
  compiled once (13 B7, B19); deep trees are freed iteratively on 3.11. **No intermediate JSON tree anywhere**: the response
  envelope borrows `result` as a raw slice, and unions peek at their tag on the raw slice and decode the chosen variant
  from it (13 B22, B23). jiter supports this directly: `current_index()` + `known_skip(peek)` +
  `slice_to_current(start)` capture a value's raw bytes without building a tree (verified on jiter 0.19.0). A union
  scans its object for the tag key while skipping values, then decodes the chosen variant from the slice with a fresh
  `Jiter`: two lexing passes, no allocation.
- A wrapper is a small pyclass `{ data: Arc<T>, bot: Option<Py<Bot>>, raw: Arc<[u8]>, cache }`. The cache has
  slots only for **non-scalar fields that are present**, not a fixed array of N (R04). `msg.chat is msg.chat` holds
  within one view because of the cache.
- Cache initialisation (R03): the child is built **outside any lock** and published with an atomic `set`; the loser
  of a race is dropped. A rare double allocation is allowed, nothing ever blocks while Python runs, and re-entrant
  initialisation is never under a lock. `PyOnceLock` is used only for process-wide globals. GC: each wrapper holds
  its own `Py` references and reports each exactly once in `__traverse__` / `__clear__`. Subinterpreters are
  unsupported (PyO3 refuses import).
- Each update's bytes are **copied out of the `getUpdates` batch buffer** (R04), so a retained child never pins a
  100-update buffer.
- **Cache seeding (D53)**: a constructor puts the objects passed to it into the child cache, so `Update(message=m).message is m`.
  The testing toolkit (14) relies on this, and it's what users expect anyway. Identity holds within one view and for
  unbound construction, not across `as_()` (D103).
- Strings: `Box<str>`/`Arc<str>` in Rust, converted to Python `str` on access (cached for repeated access).
  Small enum-like strings (`"private"`, `"text_mention"`) are interned once per process.
- **Sparse optional fields**: per type the generator splits fields into *hot* (inline `Option<T>`) and
  *cold* (`Option<Box<ColdFields>>`, or a compact sorted `(field_id, value)` vec for very wide types like
  `Message`). The hot set comes from the overlay (§02) — e.g. `Message`: `message_id, date, chat, from,
  text, entities, caption, photo, reply_markup, message_thread_id, …`.
- Unknown fields (`extra="allow"` today): kept as a raw JSON slice, exposed as `obj.raw` / `obj.raw_json` (D10, semantics in D108 below);
  `model_extra` is a deprecated alias returning unknown fields only (`{}` when none, R06). Round-tripping new Bot API
  fields keeps working before butcher catches up.
- **Unknown fields stay readable as attributes, deprecated (D105).** On an attribute miss, `__getattr__` returns the
  unknown field from raw data with a one-time `AiogramDeprecationWarning` pointing to `.raw`, for one D71 window, then
  `AttributeError`. No hot-path cost; `F.new_field` keeps matching during the window.
- **Collection fields are cached tuples (D106)**: `entities`, `photo`, the `getUpdates` result, keyboard rows.
  Identity-stable, immutable, hashable when their items are. README breaking change 23.
- Unknown union tags, enum values and update types never fail decoding. Every object exposes `.raw` / `.raw_json`.
  See [10](10-forward-compatibility.md).
- Integers: `int64` per schema `format` (217 fields) → `i64`; `int32` → `i32`; `double` → `f64`.
- Dates: Unix-time fields (overlay list, §02) are stored as `i64` and returned as `datetime` (UTC) on
  access — same public type as today. On input (B17): naive datetimes are local time, `timedelta` is seconds,
  fractional values round half-even; `from` / `from_user` and `bot` / `bot_user` are both accepted on every input path.
- Enum-valued fields return `str` (today's `use_enum_values` contract). Rust enums carry an
  `Unknown(Box<str>)` variant so new API values never break parsing. Python `aiogram.enums.*` stay `StrEnum`.

### 3.2 Bot binding (D103: independent bound views)

- `obj.as_(bot)` returns a **new view** over the same immutable data; children of a view inherit its bot. There is
  no shared mutable context and no atomics, and nothing redirects another holder's shortcuts.
- Dispatcher remounting creates a new root view in O(1) instead of the 179 µs round-trip.
- Code that uses the return value (`m = m.as_(bot)`, all generated shortcuts, the docs) keeps working. A bare
  `x.as_(bot)` statement no longer rebinds `x`; the migration checker flags it (README breaking change 22).
- Objects built by user code (`Message(...)`) are unbound, like today.
- `bot` is a reserved name (D109): colliding wire fields get an overlay rename, e.g. `bot` → `bot_user` on
  `ManagedBotCreated` / `ManagedBotUpdated`, as in 3.x.

### 3.3 Methods (`SendMessage`, …)

- Generated as `#[pyclass(frozen)]` with a `#[new]` that validates kwargs in Rust (types, unions,
  `Default` sentinels). `Default("parse_mode")` stays a Python-visible sentinel.
- Encoding is in Rust (`encode(method, bot_defaults) -> JsonBody | Multipart(parts)`), see [05](05-network.md).
- **Unreleased / custom API methods (D96–D99)**:

  | # | Decision |
  |---|---|
  | **D96** | **Raw call only**: `await bot.call("sendGift2", {"chat_id": 1, "photo": FSInputFile("a.jpg")}, returns=Message, request_timeout=None)`. User subclasses of `TelegramMethod` are **no longer supported**: generated method classes aren't subclassable, and `TelegramMethod` remains for typing and `isinstance`. Inside, the call builds an internal `RawMethod(name, params, returns)`, so request middlewares (Retry, RateLimit, logging, OTel; D43/D44/D64) and the testing toolkit (`env.on("sendGift2")`) see it like any method. README breaking change 20 |
  | **D97** | **Params** may contain `InputFile` anywhere, nested included. They are extracted into multipart attachments (`attach://…`) by the same Rust writer. Values may be aiogram types, builtins, plain dicts in wire shape, or any object with `to_dict()` |
  | **D98** | **`returns` is optional.** Omitted, it returns the decoded JSON as builtins (`aiogram.Raw`). Otherwise it is an aiogram type (Rust decoder), a builtin or container (`bool`, `int`, `str`, `list[T]`, `dict`), a class with `from_dict(data, *, bot=None)`, or any callable `(raw) -> T` |
  | **D99** | **Unknown parameters on generated methods are allowed** (`SendMessage(..., new_param=1)`), must be JSON-shaped (D87), and are forwarded as-is. A one-time `AiogramUnknownParameterWarning` per (method, name) catches typos and can be silenced by category |

### 3.4 Shortcuts (`Message.answer`, `CallbackQuery.answer`, …)

Shortcuts are synchronous: they build a method object and return the coroutine from `bot(method)`
(they never await inside). So they need no async Rust.

**Decided (O2 → D11):** shortcuts are **generated in Rust** from the overlay. The current `fill:` Python
expressions (`.butcher/types/*/aliases.yml`, `Message` has 359 lines) become a tiny declarative DSL
(`chat_id: self.chat.id`, `message_thread_id: self.message_thread_id if self.is_topic_message`). `send_copy` is
generated from a content-type mapping. Anything the DSL can't express is hand-written Rust in `<type>_ext.rs`.
There is no Python facade: one class per type, and the decoder instantiates it directly ([02](02-butcher.md) §5.1).


**Keyword-only (D100).** Every generated signature takes keyword arguments only: type and method constructors
(`#[new]` with `(*, …)`), `Bot` methods (`async def send_message(self, *, chat_id, text, …)`) and all shortcuts
(`message.answer(*, text, …)`). When Telegram makes a parameter optional or adds one, parameter order never matters,
so no signature has to be reordered and the `keep_position` ledger hack goes away. Hand-written APIs that aren't
generated from the Bot API (e.g. `bot.call(name, params)`, D96) keep their own stable signatures. README breaking change 21.
### 3.5 Python extensibility kept

| Need | v4 mechanism |
|---|---|
| Subclass a type (add methods/properties) | `#[pyclass(subclass)]`; decoder uses the registered class: `aiogram.types.register(Message, MyMessage)` |
| Store types in FSM data / pickle | `__reduce__` → `(cls._from_json, (raw_bytes,))` |
| Use types as fields in user pydantic models | `__get_pydantic_core_schema__` → plain validator `cls.from_dict` + serializer `obj.to_dict()` (wire shape); `__get_pydantic_json_schema__` returns the OpenAPI component (we have it) |
| `CallbackData` | no longer pydantic: dataclass-style with the same declaration syntax (D14, [11](11-removals.md) §4) |
| pydantic itself | not a dependency (no extra); interop hooks import it lazily if the user installed it |
| `F` / magic-filter attribute access, `isinstance` filters | normal attribute access and classes, so unaffected |
| Unreleased API methods / params | `bot.call(name, params, returns=)` and extra kwargs on generated methods (§3.3, D96–D99) |
| Dump / load / copy / introspection | **native API (D91–D94, §3.7)**: `to_json` / `to_dict` / `from_json` / `from_dict` / `replace`, in Rust **once on the base class** through a per-type vtable (13 B3), dump keys interned (B2), both `from`/`from_user` accepted on input. `model_*` stay as deprecated Python aliases |
| Lazy text (`L.key()`, `LazyProxy`) in `text`/`caption`/button `text`… | display-text fields also accept a lazy-text object and keep it as is (frozen-safe). The encoder renders it with the i18n context captured when the method was created or returned (D25, D117, 06 §3) |

Not kept: pydantic validators on aiogram types, the pydantic `model_*` kwargs beyond the alias subset (§3.7),
mutation of frozen types.

### 3.6 Model semantics (D83–D87)

| # | Decision |
|---|---|
| **D83** | **Secondary bases through ABC registration.** The primary Bot API base is the real pyclass parent. For every further base, the generator emits `SecondaryBase.register(Type)` (abc virtual subclass), so `isinstance` / `issubclass` keep working, and it generates the secondary bases' members on the type itself |
| **D84** | **Equality = same class + equal data (3.x).** A registered subclass never equals a base instance with the same fields. Hashing revised by D108: equality **ignores the bot binding** (3.x compared bots by token), and an object is hashable only if all its fields are (raw and binding excluded) |
| **D85** | **Undiscriminated unions**, 12 today (3 ever decoded): each decoded one gets a tag or an explicit predicate in the overlay (e.g. `date == 0` → `InaccessibleMessage`), otherwise the `Unknown…` variant (D10). The declaration-order fallback is **dropped** (revised by D107). Butcher `check` fails when a new undiscriminated union has no rule |
| **D86** | **Dump names** (as refined by D91–D94): `to_json()` / `to_dict()` always use wire names (`from`), i.e. what Telegram sends. The deprecated alias `model_dump()` keeps Python names unless `by_alias=True`. The deprecated alias `model_dump_json()` emits the same wire names as `to_json()` (`by_alias` ignored) but returns **`str`** (3.x return type, R06). README breaking change 18 |
| **D87** | **Extras must be JSON-shaped**, decoded and user-supplied alike: `str` / `int` / `float` / `bool` / `None` / `list` / `dict` only, stored as raw JSON, `TypeError` otherwise (3.x accepted any object). README breaking change 19. Nesting deeper than 128 levels is a decode error: a per-update `UpdateDecodeError` in polling and webhook (D10 Layer 2), `ValueError` in `from_json` / `from_dict` |

### 3.7 Native serialization API (D91–D94)

The pydantic-shaped `model_*` API is replaced by a small wire-format-centric API. The only format that matters is
Telegram's wire JSON, so dumping and loading are defined in terms of it.

| # | Decision |
|---|---|
| **D91** | **Native API, plus deprecated `model_*` aliases** for one D71 window. The aliases are thin Python on the base class. They support the common kwargs (`exclude_none`, `by_alias`, `mode`, `context={"bot": …}`) and raise `TypeError` for the rest with a hint to the native call. Per R06: `model_extra` returns unknown fields only (`{}` when none); `model_dump(exclude_unset=True)` works through the per-field "present" bitset the decoder keeps anyway; `model_copy(update=…)` maps to `replace`, which validates (3.x didn't). The codemod (D74) rewrites them |
| **D92** | **Methods on the types.** Refined by D109: reserved names are **exact** (`bot`, `raw`, `raw_json`, `to_json`, `to_dict`, `from_json`, `from_dict`, `replace`, `as_`, the `model_*` aliases), not prefixes, so `UniqueGiftColors.model_custom_emoji_id` stays legal. A colliding wire name gets an overlay rename (`bot` → `bot_user`); butcher `check` fails on a new collision until one is configured |
| **D93** | **`to_dict()` has the wire shape only**: wire names, unix ints for dates, nested builtins, no `None`. The object itself is the Python-shaped view |
| **D94** | **`model_dump_json()` = `to_json()` decoded to `str`** (wire names, R06). `model_dump()` keeps the 3.x Python-name shape while it exists |
| **D95** | **No public field introspection.** There is no `fields()`, and `model_fields` is removed rather than aliased. It can be added later without a break if real demand appears |

| Need | Native 4.0 | Deprecated alias |
|---|---|---|
| dump to JSON | `obj.to_json() -> bytes`: wire JSON, exactly what Telegram sends | `model_dump_json(...) -> str` |
| dump to builtins | `obj.to_dict() -> dict` (wire shape) | `model_dump(...)` (Python names unless `by_alias`) |
| load | `Type.from_json(data, *, bot=None)`, `Type.from_dict(d, *, bot=None)`; accept `from` and `from_user` | `model_validate(_json)(…, context={"bot": bot})` |
| copy with changes | `obj.replace(**changes)` and `copy.replace(obj, **changes)` (`__replace__`, 3.13+); validates, drops the original bytes (D108) | `model_copy(update=…)` (→ `replace`, now validating) |
| introspection | **none** (D95): stubs, docs and `inspect.signature(Type)` (generated `text_signature`) cover it; the testing toolkit uses tables generated from the IR | `model_fields` **removed** (`AttributeError` with a hint) |
| unknown data | `obj.raw` (a fresh `dict` on every access) / `obj.raw_json` (exact received bytes for wire objects, canonical `to_json()` bytes for constructed or replaced ones) (D10, D108) | `model_extra` (unknown fields only) |
| unchanged | pickle (`__reduce__`, never stale after `replace`), `__get_pydantic_core_schema__`, `repr`; `==` / `hash` per D108; `as_(bot)` returns a new view (D103) | |

What this changes elsewhere:
- `utils/serialization.py` becomes a thin wrapper over `to_dict()`; FSM storage of types uses `to_dict` / `from_dict`.
- Webhooks take raw bytes → `runner.process(bot, raw)` (12); custom web frameworks call `Update.from_json(body, bot=bot)`.
- The Rust surface shrinks to encode, decode and replace; the aliases are thin Python on the base class.
- Internal uses outside the alias subset (`dispatcher.py:280`, `aiohttp_server.py:176`) move to the native API (R06).

## 4. Free-threading notes

- `#[pyclass(frozen)]` everywhere, so all reads are lock-free (`Py::get()`). Lazy caches are built outside any lock
  and published with an atomic `set` (R03, §3.1); `PyOnceLock` only for process-wide globals.
  Bot binding is immutable per view (D103), so it needs no atomics.
- No mutable types (D15), so no `Mutex` inside pyclasses and no `&mut self` methods. Concurrent `&mut self` use
  would raise `RuntimeError: Already borrowed`.
- Python `list`/`dict` values handed out (keyboard rows, `to_dict()` results) are fresh copies or tuples, so no
  shared mutable state crosses the boundary.

## 5. Spike plan (phase 1)

1. Generate the 12 spike types + `SendMessage` with the prototype butcher (§02).
2. Benchmarks, all against the **optimised-pydantic** baseline from 09:
   - decode: realistic update, plain text update, `getUpdates`×100 **through the response path** (envelope + batch,
     not only direct `from_json`) and a `sendMessage` response (13 B24: aiogram_rust's direct-parse 7.3× was 4.0× on the
     polling path)
   - memory per update (tracemalloc + RSS for 100k retained updates), plus RSS of *accessed* trees, a single child
     retained from a 100-update batch, and GC-on sustained runs (R04)
   - attribute access: first (materialise) and warm; `F.message.text == "x"` resolve
   - `to_dict` / `to_json`, pickle round-trip, re-mount (new bound view, D103)
   - shortcut call: `message.answer(text="hi")` up to the coroutine
   - Python-subclass instantiation from the decoder (only for user `register`, not on the default path)
3. Port 2–3 hand-written helpers (`User.mention_html`, `Message.html_text`) to `*_ext.rs` + `.pyi` fragment to
   validate the D11 workflow and stubtest.
4. Gate: parse ≥3×, memory ≥4×, first access ≤2×, warm access ≤1.6× (D26; was 1.2×, which no native-getter
   design has met, see [13](13-aiogram-rust-review.md) §5), and end-to-end dispatch on a realistic router (with
   `routing_keys()`, 03 §3) no slower than optimised 3.x. Check absolute µs as well as ratios, because the
   baseline keeps getting faster. The gate is binding and has no pre-committed fallback (D104): if it fails, the
   model layer is redesigned from scratch, and every decision that assumes Rust-native types (D4, D11, D14, D53
   mechanism, D83–D87, D91–D95, D102, D103) is reopened.
5. Cache/GC/teardown tests (R03): concurrent first access returns one wrapper, callback re-entry can't deadlock,
   cycles through Bot/session are collectable, teardown works on 3.11 and free-threaded builds.
6. Method: warm process (20 real requests first) on **pyo3 ≥0.30**, with `Py` objects already released while
   detached, so pyo3's reference-pool mutex is armed as in a running bot. GC off, median of 7, A/B in one
   session, Linux + uvloop as well as macOS. Attribute each change through a small build matrix (13 §1).
