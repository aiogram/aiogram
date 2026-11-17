# 06 — Utils: what moves to Rust, what stays

With Rust-native types (D4), the main reason Rust didn't help utils goes away. Today the cost is building
pydantic `MessageEntity` objects and reading their attributes, roughly 50 ns per getattr and 2–8 µs per
construction. In v4 the entities already live in Rust.

## 1. Moves to the Rust core

| Item | Today | v4 |
|---|---|---|
| `TextDecoration.unparse` (`utils/text_decorations.py:96,111`); `Message.html_text` / `md_text` | HTML 22 µs, MarkdownV2 33 µs (230 chars, 6 entities); recursive generator + `filter()` sub-list per entity, O(n²) | Rust renders from the Rust entity list with native UTF-16 offsets, in one stack pass |
| UTF-16 helpers (`sizeof`, offset slicing) | 0.74 µs per 300 chars, recomputed at every nesting level in `formatting.py` | Rust function; `Text.render` gets lengths back instead of re-encoding |
| Markdown / HTML quoting | `html.quote` 1.4 µs, MD quote 4.4 µs (230 chars) | Rust |

**Extensibility rule**: users subclass `TextDecoration` and override `bold`/`link`/`quote`… The Rust fast
path is used only for the two built-in instances (`html_decoration`, `markdown_decoration`) and exact built-in
types. Any subclass runs the Python algorithm, which also gets the O(n) rewrite. The Python implementation stays
as the reference and is parity-tested against Rust on a corpus of entity layouts (nested, overlapping, surrogate
pairs, `expandable_blockquote`, custom emoji, date_time).

## 2. Stays Python (fixes listed in [09](09-3x-quick-wins.md))

| Item | Cost | Why not Rust |
|---|---|---|
| `KeyboardBuilder.export` deepcopy (`utils/keyboard.py:161,171`) | 30 btn 4.4 ms, 100 btn 46 ms | O(n²) bug; a shallow copy is 10×+ faster. In v4 buttons are immutable Rust objects, so no copy is needed at all |
| `deserialize_telegram_object` (`utils/serialization.py:15,56`) | 4.5 ms (99% builds an SSL context via a throwaway `Bot`) | caching bug; v4 keeps its semantics on top of the encoder (R18): encoder output plus the method name, with defaults resolved and files extracted |
| `CallbackData.pack/unpack` (`filters/callback_data.py:83,109`) | 2.3 / 2.9 µs | rewritten without pydantic in Python (D14, 11 §4); prefix fast-fail before split+convert |
| `aiogram.utils.markdown` | — | removed (D13) |
| magic-filter `_resolve` | 0.77 µs | external dependency, each step calls Python |
| WebApp HMAC (`utils/web_app.py:121-140`) | 10.7 µs | `hashlib` is C; optionally cache the derived secret |
| Ed25519 third-party check (`utils/web_app_signature.py`) | 283 µs | already `cryptography` (Rust/OpenSSL) |
| deep links, token validation, auth widget, i18n, media group builder, chat_action, backoff | <3 µs each, or asyncio sleeps | noise |
| `from unittest.mock import sentinel` (`types/base.py:2`, `dispatcher/event/bases.py:5`) | ≈25 ms import | v4 only; the 3.x quick win was dropped (D120) |

## 3. i18n absorbed into core (D25)

Why: `aiogram_i18n`'s `LazyProxy` relies on pydantic, and with D4 aiogram types aren't pydantic any more. So
lazy text in keyboards and captions would stop working, and fixing it needs core support either way.
aiogram_rust hit the same wall and absorbed it (13 §4). All of this stays **Python**; only the encode-time hook
touches Rust.

| Piece | Design |
|---|---|
| Engines ("cores") | `GettextCore` built in (`.mo`/`.po`, as 3.x `I18n`); `FluentRuntimeCore` / `FluentCompilerCore` behind extras `aiogram[fluent-runtime]`, `aiogram[fluent-compiler]`; custom engine = `BaseCore` subclass |
| Locale managers | `UserLocaleManager` (reads `event_context.user.language_code`, no I/O, the default), `FSMManager(fallback=…)`, `ConstManager`; custom = `BaseManager` subclass |
| Handler API | `I18nContext` injected as `i18n`: `i18n.get("key", **kw)`, `i18n.key(**kw)`, `i18n.locale`, `i18n.use_locale(...)` |
| Lazy text | `L.key(**kw)` / `LazyProxy("key")`: an object implementing a small render protocol. Display-text fields (`text`, `caption`, `title`, button `text`, …; marked in the overlay, 02 §3) accept it and store it unchanged, so it works with frozen types (D15). The Rust encoder renders it when the request is built, with the i18n context **captured at return** (D117): a method created inside an update, or returned from a handler, captures the current locale, which covers webhook inline replies and polling silent calls. Rendered once per request snapshot; retries reuse it. One keyboard literal then serves every locale |
| Filters | `LazyFilter("key")` matches the text against the key in the current locale |
| Context | one module-level `ContextVar` set by the middleware, captured by methods at creation/return (D117), so encoding after the handler returned still renders with it. Outside handlers, `i18n.use_locale(...)` or the engine default applies |
| 3.x compatibility | `aiogram.utils.i18n` names kept: `I18n`, `gettext`/`_`, `lazy_gettext`/`__`, `I18nMiddleware`, `SimpleI18nMiddleware`, `ConstI18nMiddleware`, `FSMI18nMiddleware`, now as thin wrappers over the new engine. **No renames**, unlike aiogram_rust |
| `aiogram_i18n` | **deprecated**: the migration guide maps its API one to one onto core; only one final release, carrying the deprecation notice and pointing to the guide |
| Tooling | key extraction / checking stays external ([FTL-Extract](https://github.com/andrew000/FTL-Extract)) and must recognise `i18n.get`, `i18n.key()`, `L.key()`, `LazyFilter` |

Risks:
- Fluent packages' free-threading readiness is unknown; they're added to the 07 §4 watch list.
- Rendering lazy text at encode is a Python callback per lazy field. That is cheap, but the encoder must not
  hold Rust locks while it runs (07 §2).

## 4. Utils API (D59–D62)

Defaults:
- **Generated from the IR (02)**, because these copy type fields by hand today and drift on every Bot API bump:
  - `InlineKeyboardBuilder.button()` / `ReplyKeyboardBuilder.button()` signatures;
  - `MediaGroupBuilder.add_*()`, with `Default("parse_mode")` instead of `UNSET_PARSE_MODE` (11 §1);
  - `ChatActionSender.<action>()` constructors, from `ChatAction`;
  - `Text.as_*_kwargs()`, one helper per IR triple `X` / `X_entities` / `X_parse_mode`, plus a generic `as_kwargs_for("X")`.

  Runtime bodies delegate to the type constructors, so only signatures and docs are generated.
- **Builders stay mutable and fluent** and produce immutable types (D15); no deepcopy is needed.
- **Unchanged APIs**: deep linking / payload, WebApp and auth-widget checks (frozen dataclasses, 11 §4), Ed25519 signature,
  `CallbackAnswerMiddleware`, `ChatActionMiddleware`, `backoff`, `token`, `link`, `class_attrs_resolver`.

| # | Decision |
|---|---|
| **D59** | ~~Opt-in album aggregation (`MediaGroupMiddleware`)~~ **Withdrawn (D116, see 19)**: album aggregation is deferred out of 4.0. Per-handler buffering can't work behind the FSM lock (D27/D28 take it before routing), and the ingress designs are too risky for 4.0. To revisit as a Runner pre-dispatch stage |
| **D60** | **Bot commands from handlers** (cf. PR #1867): `Command(...)` gains optional `description=`, `scope=` (a `BotCommandScope`), `language_code=` and an i18n key (D25) for localised descriptions. `router.resolve_bot_commands()` returns `{(scope, language): [BotCommand, …]}` across the tree. `await dp.set_my_commands(bot, *, delete_missing=False)` calls `setMyCommands` for each `(scope, language)`. Nothing is sent automatically. `CommandStart` / hidden commands (`description=None`) are excluded |
| **D61** | **Lazy text in formatting trees**: `Text` nodes may contain lazy values (`Bold(L.title()), " ", L.body()`). A `Text` that contains one implements the lazy-text protocol (06 §3), and its text **and entities** (UTF-16 offsets) are rendered once per request snapshot with the i18n context captured at return (D117). Explicit `entities` / `parse_mode` next to a lazy `Text` raise. A plain `Text` renders eagerly as today |
| **D62** | **Both formatting styles stay; formatting nodes are primary.** Docs lead with `aiogram.utils.formatting`: it is entity-based, so there are no escaping bugs, and it works with D61. `html` / `md` decorations stay supported for `parse_mode` users and for `html_text` / `md_text` unparse (Rust fast path, §1) |

## 5. Security notes (if any signature check is ever rewritten)

Constant-time comparison (`hmac.compare_digest` today, `web_app.py:140`, `auth_widget.py:24`); parse init data
exactly like `parse_qsl(strict_parsing=True)` (last duplicate key wins, same `+`/percent decoding), so the
checked string equals the returned data; ed25519 **strict** verification; lowercase-hex comparison. Not planned
for Rust.
