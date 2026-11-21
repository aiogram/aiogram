# Threat model: aiogram

## What this project does and where untrusted input enters

aiogram is an asynchronous Python framework for Telegram bots. It contains a Bot API client over aiohttp,
a dispatcher (routers, observers, filters, middlewares, dependency injection), a finite state machine (FSM)
with memory, Redis and MongoDB storages, an aiohttp webhook integration, and helpers for Telegram Mini App
`initData`, the Login Widget, deep links, callback data and i18n. Developers build bots on top of it;
it is not a standalone service.

Attackers, most important first:

1. **Any Telegram user, chat or bot that can send updates to the bot.** Assume every field another user can set
   is attacker-controlled: message text, entities and their URLs, captions, file names, `callback_data`, inline
   queries, `/start` deep-link payloads, `web_app_data`, `language_code`, chat titles, usernames, and so on.
2. **Anyone who can reach the webhook endpoint directly**, bypassing Telegram: the request path (including the
   bot token in the path for `TokenBasedRequestHandler`), headers (`X-Telegram-Bot-Api-Secret-Token`,
   `X-Forwarded-For`) and the JSON body.
3. **A Mini App or browser client** that sends `initData` or Login Widget data to the developer's backend for
   verification with `aiogram.utils.web_app`, `aiogram.utils.web_app_signature` or `aiogram.utils.auth_widget`.

Trusted: the bot token, the developer's handlers, filters, middlewares and configuration, the FSM storage
server (Redis/MongoDB), the process environment, and the file system paths the developer passes to aiogram.

The Telegram Bot API server is treated as an honest relay. Data that only the server controls (response
bodies, `file_path`, the files served by a self-hosted `telegram-bot-api` in local mode) matters less than
data another user controls. A report that needs a malicious or compromised Bot API server, or a developer-
configured custom `TelegramAPIServer`, must say so.

## Components that matter most

1. **Webhook ingress**: `aiogram/webhook/aiohttp_server.py`, `aiogram/webhook/security.py`.
   Of interest: bypass of the secret-token check, IP-filter bypass, `TokenBasedRequestHandler` accepting
   requests or tokens it should not, an update processed for the wrong bot, unbounded resource use per request,
   background-task handling that loses or duplicates updates.
2. **Signature checks**: `aiogram/utils/web_app.py`, `aiogram/utils/web_app_signature.py`,
   `aiogram/utils/auth_widget.py`. Of interest: forged or tampered data accepted as valid, differences between
   the string that is verified and the object returned to the caller, non-constant-time comparison,
   exceptions instead of a `False` result on malformed input.
3. **Dispatcher, routing, filters and middlewares**: `aiogram/dispatcher/`, `aiogram/filters/`
   (`command.py`, `callback_data.py`, `state.py`, `chat_member_updated.py`), `aiogram/utils/magic_filter.py`.
   Of interest: a crafted update that skips a filter or middleware so a handler runs that should not, an update
   attributed to the wrong user, chat, thread or business connection
   (`aiogram/dispatcher/middlewares/user_context.py`), `CallbackData.unpack` type confusion, an exception from
   attacker input that stops the polling loop or the webhook worker.
4. **FSM state and isolation**: `aiogram/fsm/` (`context.py`, `middleware.py`, `strategy.py`, `scene.py`) and
   `aiogram/fsm/storage/` (`base.py` key builder, `memory.py`, `redis.py`, `mongo.py`, `pymongo.py`).
   Of interest: one user reading or writing another user's or chat's state or data (key collisions, strategy
   mistakes), isolation locks that do not serialize what they claim, state leaking between bots.
5. **Formatting and escaping**: `aiogram/utils/text_decorations.py`, `aiogram/utils/formatting.py`,
   `aiogram/utils/markdown.py`. Of interest: attacker text or entity attributes (URLs, language, custom emoji
   ids) that inject markup, links or entities into the HTML / MarkdownV2 the bot sends.
6. **Deep links and payloads**: `aiogram/utils/deep_linking.py`, `aiogram/utils/payload.py`.
7. **Bot API client**: `aiogram/client/bot.py`, `aiogram/client/telegram.py`, `aiogram/client/session/`,
   `aiogram/types/input_file.py`. Of interest: the bot token leaking into logs, exception messages or reprs;
   request smuggling or parameter injection into Bot API calls from user-controlled values; downloads that
   write or read outside the intended location; TLS verification being weakened.

Also in scope, but less important: `aiogram/utils/i18n/`, `aiogram/utils/media_group.py`,
`aiogram/utils/chat_action.py`, `aiogram/utils/callback_answer.py`, `aiogram/utils/keyboard.py`,
`aiogram/utils/token.py`, `aiogram/utils/serialization.py`.

Generated code in `aiogram/types/`, `aiogram/methods/` and `aiogram/enums/` mirrors the Telegram Bot API and
is produced from `.butcher/`. It is in scope only where a flaw is in aiogram's own logic (base classes,
validators, defaults, shortcuts), not for API fields Telegram itself defines.

## How to exercise it

- The checkout is at `/src` with a uv virtualenv at `/src/.venv` already on `PATH`, all runtime extras
  installed except docs. Run `pytest tests -q` from `/src`; it is fully offline (HTTP is mocked with `aresponses`).
- Redis storage tests are skipped unless a server is given. `redis-server` is installed in the image:
  `redis-server --daemonize yes && pytest tests --redis redis://localhost:6379/0`. MongoDB is not installed,
  so MongoDB tests are skipped.
- `tests/mocked_bot.py` (`MockedBot`) records outgoing API calls without network access.
  `Dispatcher.feed_update()` / `feed_raw_update()` feed an update through routers, filters and middlewares.
  `aiohttp.test_utils.TestClient` (via `pytest-aiohttp`, see `tests/test_webhook/`) drives the webhook handlers.
- Write PoCs as small pytest files that build a `Dispatcher`/`Router` or webhook app with documented APIs and
  feed a crafted `Update` JSON or HTTP request. Never contact `api.telegram.org`.

## How we rate severity

- **Critical**: code execution in the bot process from an update or webhook request; forged `initData` or Login
  Widget data accepted by the check functions with the correct bot token or Telegram public key; webhook
  authentication bypassed so an unauthenticated peer can inject updates when `secret_token` is configured.
- **High**: one Telegram user reading or writing another user's or chat's FSM state or data under the default
  strategy and key builder; a crafted update that bypasses a documented filter or middleware so a protected
  handler runs; disclosure of the bot token to a third party; injection of links or markup into messages through
  aiogram's escaping helpers; a single small update or request that stops the polling loop or webhook worker,
  or blocks the event loop, under default settings.
- **Medium**: the same issues when they need a non-default but documented option (custom key builder, isolation
  or storage settings, `TokenBasedRequestHandler`, IP filter behind a proxy, local Bot API server mode);
  information disclosure; resource use far out of proportion to the input size.
- **Low**: an exception confined to one update that the dispatcher handles; DoS that needs volume rather than a
  crafted input (rate limiting is the job of the application or the reverse proxy); hardening suggestions.

Anything that needs a malicious Bot API server ranks one level below the same issue triggered from a field another
user controls. A report without a runnable reproducer is capped at Medium.

## Anything to leave alone

- Vulnerabilities in dependencies themselves (aiohttp, pydantic, magic-filter, aiofiles, redis-py, motor/pymongo,
  aiohttp-socks, Babel, cryptography), unless aiogram uses them in an unsafe way.
- Developer misuse: trusting `initDataUnsafe` or `parse_webapp_init_data()` output without checking it,
  handlers without the filters they need, sending user text with a `parse_mode` without the escaping helpers,
  a webhook without `secret_token`, passing user-supplied URLs to `URLInputFile` or paths to `FSInputFile` /
  `download()`, user-controlled keys in FSM data, sharing a storage between bots without `with_bot_id=True`.
- Replay of signed `initData` or Login Widget data: aiogram only verifies integrity; freshness (`auth_date`),
  replay protection and session binding are the application's job.
- Callback data and deep-link payloads are not signed by design; their contents are user input.
- The bot token being visible to anyone who already controls the process, its environment, or the host.
- Deviations from the Bot API specification with no security consequence; Telegram-side behaviour.
- `docs/`, `examples/`, `tests/`, `scripts/`, `.butcher/` and `.github/`.

## Reports and patches

- Include the aiogram commit, Python version, extras or storage backend used, the developer configuration the
  issue needs, and the crafted update JSON or HTTP request.
- Propose a minimal patch against `dev-3.x` with a pytest regression test in the matching `tests/` module, and no
  unrelated refactoring. For generated files (`aiogram/types`, `aiogram/methods`, `aiogram/enums`) change the
  `.butcher/` source instead.
- Report one finding per root cause and list every entry point it reaches.
