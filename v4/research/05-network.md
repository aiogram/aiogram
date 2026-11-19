# 05 — Network: session, encoder/decoder, webhook

Verdict (D5): **keep aiohttp and `BaseSession` in Python**. Move only the CPU-bound
**encode/decode** to the Rust core. No Rust HTTP client and no Rust webhook server.

## 1. Today

`Bot.__call__` (`bot.py:572`) → session middleware chain rebuilt per call (`session/base.py:261-268`,
`manager.py:53-61`) → `make_request` (`aiohttp.py:161`) → `build_form_data` (`aiohttp.py:145-159`:
`model_dump()` then recursive `prepare_value`, `base.py:188-259`, which resolves `Default`, extracts files to
`attach://`, `json_dumps` per nested field) → `FormData` (urlencoded or multipart) → `resp.text()` →
`check_response` (`base.py:76-149`) → `Response[T].model_validate_json` → error mapping.

`SendMessage` with a 3×3 keyboard + 3 entities:

| Step | µs |
|---|---|
| `model_dump()` | 20.8 (keyboard alone 10.9: ≈12 `None` fields per button) |
| `prepare_value` (195 recursive calls) | 33.1 |
| `build_form_data` + `FormData` encode | **93** |
| JSON body alternative (`to_json(model_dump(exclude_none))`) | 21.4 |
| `check_response` on a 979 B reply | 47 (JSON decode 3, the rest is model construction) |
| `getUpdates` ×100 | 4 930 (49/update) |
| End-to-end loopback, aiogram vs raw aiohttp | 330 vs 146 µs CPU/req (asyncio); uvloop gave no gain on the aiogram path |

Real round-trips to `api.telegram.org` take 20–200 ms. At 30 msg/s the whole network layer is ≈1% of a core;
it matters for broadcasts (≈1 000 msg/s ≈ 33% of a core) and big `getUpdates` batches.

## 2. v4 design

### 2.1 Encoder (Rust core)

```python
body = _core.encode(method, defaults=bot.default)   # -> JsonBody(bytes) | Multipart(fields, files)
```

- Walks the Rust method struct directly: no `model_dump`, no Python recursion.
- Resolves `Default(...)` against `DefaultBotProperties` (converted to a Rust struct once per bot).
- Value rules (B17, also 01 §3.1): `timedelta` as seconds, naive datetimes as local time, half-even rounding;
  `timeout <= 0` means no deadline.
- Lazy text (D117) is rendered once per request snapshot with the i18n context captured when the method was
  created or returned; text **and** entities come from that one render, and retries reuse it.
- No files → **`application/json` body** (the Bot API accepts it; the schema documents JSON bodies for all
  methods). Files → multipart: the schema's `encoding` map tells which parts are JSON-encoded. `InputFile`
  objects are returned to Python as `(name, InputFile)` pairs, and Python streams them (`InputFile.read()`
  async generators stay Python).
- Generic path for `bot.call(...)` raw calls (`RawMethod`, 01 §3.3 D96–D98): params walked once, files extracted, same writer.

### 2.2 Decoder (Rust core)

```python
result = _core.decode_response(method_cls, raw_bytes, bot)   # Response[T] without pydantic
```

- `{"ok": true, "result": …}` decoded straight into the method's return type (from the schema's
  `mediaTypes`, e.g. `MessageOrTrueResult`). Bot is bound once in the root view (D103, 01 §3.2).
- `{"ok": false, …}` → `(error_code, description, parameters)` handed to Python, which maps them to the 3.x
  exception classes with `e.reason` (`ErrorReason`, D47).
- `getUpdates` decodes the array into a tuple of `Update` in one call.
- **No intermediate tree (13 B22)**: the envelope is parsed by borrowing `result` as a raw byte slice, and the
  typed decode reads it in place (unions lex their slice twice, 01 §3.1). For `getUpdates`, each element's slice is
  decoded on its own and its bytes copied out of the batch buffer (R04), which gives per-update isolation and
  `update.raw` (D10). aiogram_rust: 6.2 → 3.8 µs per batched update,
  `sendMessage` 3.0 → 2.0 µs.

### 2.3 `BaseSession` contract (unchanged for users)

- `make_request`, `stream_content`, `close` stay abstract. Users' httpx/other sessions keep working.
- `prepare_value` / `check_response` stay overridable. The Rust fast path is used only when
  `type(session).prepare_value is BaseSession.prepare_value` and the JSON hooks are defaults; otherwise the
  old Python path runs, so subclasses don't break.
- `json_loads` / `json_dumps` hooks stay. Default `json_dumps` → Rust core (`_core.to_json`) that understands
  aiogram types; `json_loads=None` keeps meaning "decode in core". JSON hooks may return `str` or `bytes` (R18).
- `TelegramMethod.to_json()` is the model representation (unresolved `Default` omitted) and raises for
  `InputFile` values; the ready request is built only by the encoder (R18).
- Request middlewares (`RequestMiddlewareManager`) keep their API; the chain is prebuilt and rebuilt only on
  `register`/`unregister`.
- `TelegramAPIServer` (local Bot API) unchanged.

### 2.4 Webhook

- Read the body as bytes and call `_core.decode_update(raw, bot)`. Drop `request.json()` +
  `model_validate`. Saves the dict round-trip (101 → ≈84 µs today, far more with Rust types).
- Webhook replies (R18): JSON when the method has no files, **multipart** otherwise (the encoder already returns
  `JsonBody | Multipart`), instead of building a `MultipartWriter` for every reply (`aiohttp_server.py:334-358`).
- Background mode has a pending cap (`max_pending`, R12); beyond it the handler answers 5xx so Telegram redelivers.
- Add an **ASGI-neutral handler** (raw bytes in, status + bytes out) next to the aiohttp one, so users can
  run Granian/uvicorn without aiogram shipping a Rust server.

## 2.5 Client features (D43–D46)

| # | Decision |
|---|---|
| **D43** | **Opt-in `RetryMiddleware`** (request middleware, `aiogram.client.session.middlewares`): `bot.session.middleware(RetryMiddleware(max_retries=3, max_wait=30))`. **429** is retried after `retry_after`, which is always safe because Telegram didn't execute the request. If `retry_after > max_wait`, it raises immediately. **Network errors / 5xx** are retried with `backoff` only for methods marked `idempotent` in the generated metadata (plus user overrides, `retry_methods=`), not by a `get*` prefix; `getUpdates` is excluded (the Poller owns it), and sends are never retried (risk of duplicates). `RetryMiddleware` is outermost. Uploads are retried only when every `InputFile` is `replayable` (True for built-ins). Lazy text is rendered once per request snapshot (R19). Nothing changes unless it is installed |
| **D44** | **Opt-in `RateLimitMiddleware`**: token buckets per event loop, `global_rps=30`, `per_chat_rps=1`, `per_group_per_minute=20`, all configurable because Telegram's limits are approximate and can change. It waits instead of sending. The chat key comes from the method's `chat_id`; methods without one count only against the global bucket. It sits inside `RetryMiddleware` and charges **every attempt**, refunding tokens on cancel-while-waiting (R19). Under free-threading the buckets are per loop, so a multi-thread setup divides the limits explicitly (documented) |
| **D45** | **Sessions stay per bot** (3.x). The docs show sharing one session across many bots, plus `close_bot_session=False` / `Runner.add_bot(..., close_session=False)` (12 §5) |
| **D46** | **Downloads**: `timeout` becomes per-phase (`connect`, `sock_read` idle) with no total cap by default and an optional `total=`. New `async for chunk in bot.stream(file_or_path, chunk_size=…)`. Typed overloads: a path destination returns `None`; `BinaryIO` / `None` returns `BinaryIO`. Old kwargs are still accepted; an int `timeout=` maps to `total=` for compatibility. The stream is closed on every path, which fixes the traceback leak (13 §4) |

Defaults unchanged: request middlewares, proxies (`aiohttp_socks`), `TelegramAPIServer` / local mode,
`bot.me()` caching. `bot.id` is computed once at init.

## 3. Rejected

- **Rust HTTP client (reqwest/hyper + pyo3-async-runtimes)**: each call hops tokio → `call_soon_threadsafe`
  (self-pipe, thread hop), costing tens of µs and eating most of aiohttp's ≈60–80 µs client cost. A second
  runtime beside asyncio breaks `os.fork` (gunicorn preload). It would lose aiohttp-socks chains/SOCKS4,
  custom `ssl.SSLContext`/certifi and aiohttp trace configs, and leave cancellation edges fragile. Gain is under
  10% CPU on a network-bound path.
- **Rust webhook server**: aiohttp's server costs ≈60–70 µs/request against ≥47 µs parse plus handlers;
  Telegram opens at most 100 connections. The ASGI handler covers users who want a faster server.
