# aiogram.test invariants

The rules `aiogram.test` ("Testing World") keeps. A change that breaks one of them is a
regression unless this file changes in the same commit. Each bullet names the test file in
`tests/test_testing/` that guards it, where one is obvious.

Terms used below:

- **Setup gap**: `WorldLookupError`. The test's own setup is missing something, or the
  toolkit does not model that surface. Nothing converts it into a Telegram error.
- **Telegram rejection**: an `ApiRejection` that `handle_call` turns into the framework's
  own exception (`TelegramBadRequest`, `TelegramForbiddenError`, `TelegramRetryAfter`).
- **Modeled**: the call changes world state and its result agrees with that state.
- **Record-only**: the call is logged and answered with a synthesized, schema-valid result.

## Isolation and lifecycle

- A blueprint holds no mutable runtime state. Building an environment never mutates it. [test_blueprint.py]
- One blueprint can build any number of independent environments, at any pytest scope. [test_blueprint.py]
- Each environment owns its own `Bot`, `Dispatcher`, FSM storage, world, call log and overrides. [test_environment.py]
- The environment's `Bot` session never does network I/O and needs no real token. [test_session.py]
- The `Bot`, `Dispatcher` and FSM storage the environment exposes are the same objects handlers get through DI. [test_environment.py]
- Nothing one test does is visible to another: messages, memberships, join requests, outstanding queries, FSM state, overrides, recorded calls, profile, invite links, sticker sets, file content. [test_plugin.py]
- Isolation holds even when the blueprint fixture is session-scoped. [test_plugin.py]
- Disposal (sync or async) closes the bot session and FSM storage and leaves no pending task or open resource. [test_environment.py]
- Disposal never drains background tasks on its own. [test_environment.py]
- A disposed environment holds no task. [test_task_pruning.py]
- The wait timeout is configuration, not state: two worlds that differ only in it compare equal. [test_waiting.py]

## Blueprint and world declaration

- A blueprint declares chats, users, memberships, the bot's identity and `DefaultBotProperties`. [test_blueprint.py]
- `bot.me()` returns the declared bot identity. Outgoing `Default(...)` sentinels resolve from the declared defaults. [test_defaults.py]
- A user's private chat with the bot need not be declared. It opens on demand, shaped like a declared one, on user-driven paths only: following a link, an unbound actor sending, an actor binding to its own id, `env.chat(user_id)`, a wait naming a user. [test_world.py]
- A group, supergroup or channel that was never declared is never invented. Binding to one is a setup gap. [test_world.py]
- An id already taken raises `ValueError`, in a blueprint and in a running world alike. [test_runtime_additions.py]
- An entity added without an id gets the next free one, from the same allocator the blueprint uses. [test_runtime_additions.py]
- `env.add_user/add_private_chat/add_group/add_supergroup/add_channel` are the blueprint methods run on a scratch blueprint: same signature, same shape, equal result. [test_runtime_additions.py]
- Adding entities to a running environment never changes its blueprint or any other environment. [test_runtime_additions.py]
- `env.add_*` returns the live handle `env.user()` / `env.chat()` would return. [test_runtime_additions.py]
- Members are named by spec, by actor or by id. A member the world lacks is a setup gap naming `add_user`. [test_runtime_additions.py]
- The bot's own status in a chat is declared by `bot_status=` or by naming `blueprint.bot` in `members`. Using both is rejected, even with the default status. [test_chat_administration.py]
- Absent a declaration, the bot is a plain member of every group, supergroup and channel. [test_bot_rights.py]
- Administrator rights and restricted permissions are declared state, never invented on read. They are declared through `Blueprint.set_member`, for any member, the bot included. [test_chat_administration.py]
- An administrator declared with no rights reads back the ordinary administrator rights. [test_chat_administration.py]
- `administrator_rights(...)` gives the ordinary rights with only the named overrides applied. [test_chat_administration.py]
- A member declared with permissions reads as restricted. Restricted with no permissions denies every permission. [test_chat_administration.py]
- Declaring both rights and permissions for one member is rejected. [test_chat_administration.py]
- What a blueprint declares reads back as the same state API calls would reach: permissions get their documented defaults, a declared topic goes through the `createForumTopic` path, a declared poll sits on a message in its chat. [test_world.py]
- A group or supergroup grants every member permission by default. This is the toolkit's convention, documented as such; `permissions=` declares a stricter one. [test_default_chat_permissions.py]
- A private chat and a channel have no member permissions. [test_default_chat_permissions.py]
- `default_chat_permissions()` returns a new object each call, and the Bot API couplings leave it unchanged. [test_default_chat_permissions.py]
- `getChat` and the bot's send checks read the same chat permissions. [test_default_chat_permissions.py]
- Declaring topics on a chat makes it a forum. A supergroup can also be declared a forum with no topic. [test_topics.py]
- Another bot is declared with `add_user(..., is_bot=True)`. [test_other_actors.py]
- `bot_to_bot_mode=` on `add_user` is accepted only for a bot; on a person it raises `ValueError`. `Blueprint(bot_to_bot_mode=...)` sets the bot's own, off by default. [test_other_actors.py]
- `Blueprint(bot_group_privacy=...)` is on by default. `getMe` and the cached `me()` report `can_read_all_group_messages` as its negation, also after `world.bot_group_privacy` changes, and `me()` makes no call. [test_other_actors.py]

## Chat registry and ownership

- Every chat in a world's registry is wired to that world, however it got there, including after the whole mapping is replaced. [test_world.py]
- Registering a fresh chat (one that belongs to no world) always succeeds. A plain mapping is wrapped into a fresh registry. [test_world.py]
- Re-registering a chat in its own world is a no-op. [test_world.py]
- Registering a chat owned by a different world is refused on every path: whole-mapping assignment, `dict(other.chats)`, item assignment, bulk updates. [test_world.py]
- A refused registration leaves the donor's chat wired to the donor and bound to the donor's bot. [test_world.py]
- A chat moves between worlds only explicitly: detach it first, or pass an independent copy or one rebuilt from the declaration. The registry never guesses. [test_world.py]
- Every remedy a refusal message prints runs as written, detaching step included. [test_world.py]
- The whole-mapping refusal points at building the wanted world, not at transplanting chats. [test_world.py]

## Actors and triggers

- A trigger builds a schema-valid `Update` and feeds it through `Dispatcher.feed_update`. Filters, middlewares, DI, FSM and routers all run. [test_triggers.py]
- A trigger returns the handler's return value. [test_triggers.py]
- Extra keyword arguments to a trigger reach filters, middlewares and handlers through DI. [test_triggers.py]
- The update's sender and chat come from the actor and its binding; `event_from_user` and `event_chat` resolve to them. [test_triggers.py]
- Every `Update` variant the framework defines has a trigger. The test over the full set declares no exemptions. [test_triggers.py]
- Each trigger produces an update shaped as Telegram would deliver it. [test_triggers.py]
- A post in a declared channel is a `channel_post`, not a `message`. Editing one is an `edited_channel_post`. [test_triggers.py]
- `stopped_message_generation` is only about the actor's own private chat with the bot, keeps the topic thread when bound to one, and is a setup gap from any other chat. [test_triggers.py]
- Binding an actor derives a new actor. The original keeps its binding. [test_topics.py]
- An actor bound to a topic produces updates with that `message_thread_id` and `is_topic_message`. [test_topics.py]
- The send trigger takes a reply target (message or stored id). An id resolves to the chat's stored object, not a copy. `reply()` is the same thing. [test_reply_sugar_and_click_hints.py]
- An explicit `reply_to_message` in `fields=` wins over the reply target, as field overrides win everywhere. [test_reply_sugar_and_click_hints.py]
- A text or caption a user actor sends or edits gets the `bot_command` entities Telegram attaches, UTF-16 offsets. [test_bot_command_entities.py]
- Passing `entities` / `caption_entities` (even empty) replaces the computed ones. The bot's own messages never get added entities. [test_bot_command_entities.py]
- A bot command is: a slash at the start or after a char that is not a letter, digit, `_`, `/`, `<`, `>`; then 1–64 ASCII letters/digits/underscores; optionally `@` plus 3–32 of them; not followed by a letter, digit, `_`, `/`, `<`, `>`. A rule broken anywhere, the `@name` included, means no entity. [test_bot_command_entities.py]
- A user's edit trigger sets `edit_date` and changes only the fields passed. Editing a message the actor did not send is a setup gap. [test_actor_alignment.py]
- An edited message fed by hand replaces the stored message with the same id. [test_actor_alignment.py]
- An inline query's `chat_type` is `sender` for the actor's private chat with the bot, else the chat's type. [test_actor_alignment.py]
- The subscription trigger accepts only `active`, `canceled`, `failed`. A subscription payment carries its expiry date and first-recurring flag. [test_actor_alignment.py]
- A guest message carries a world-unique `guest_query_id`, takes field overrides, and its message is registered like other carried messages. Answering it is record-only. [test_actor_alignment.py]
- A business connection update names the account owner as its user, whoever triggers it. [test_actor_alignment.py]
- Every trigger that feeds an update takes keyword `deliver=True`. With `deliver=False` the world changes and every message is stored exactly as when delivered, and nothing is fed. [test_withheld_updates.py]
- A withheld trigger returns `Withheld` with a reason (naming `deliver=False` when the test chose it) and the withheld update, bound to the bot. `create_topic()` returns the new topic instead. [test_withheld_updates.py]
- A withheld trigger opens an empty route scope of its own: `routes` is empty, `last_route` is `None`, `assert_updates_handled()` has nothing to flag. [test_withheld_updates.py]
- A withheld callback query can still be answered. [test_withheld_updates.py]

### Clicks

- A click resolves `callback_data` from a real button on a stored message; the update's `data` and `message` come from them. [test_triggers.py]
- A click given a message resolves the stored version in the actor's chat (a stale copy yields the edited message) and requires the `callback_data` to be on it, else a setup gap. [test_actor_alignment.py]
- A click that misses in the actor's chat but matches a button in another known chat names that chat and suggests binding there. With no match anywhere, no such hint is given. [test_reply_sugar_and_click_hints.py]
- Buttons are searched in document order: inline keyboard first, then rich blocks at any depth. A rich button object can be passed directly. [test_rich_messages.py]

### Membership triggers

- In a group or supergroup, join and add-bot also post a `new_chat_members` service message, after the membership update. [test_membership_triggers.py]
- The announcement is suppressible per call. A private chat never gets one. Leave and remove-bot never post one. [test_membership_triggers.py]
- A join or add-bot trigger returns the membership update's handler result, announcement or not. [test_membership_triggers.py]
- `promote()` / `demote()` default the subject to the bot and accept a declared user, a resolved state or a bare id. [test_membership_triggers.py]
- `promote()` grants exactly the rights named. Naming none still promotes, with every right denied. [test_membership_triggers.py]
- `promote()` with an unknown right keyword raises at the call site, naming the real fields. [test_membership_triggers.py]
- Dispatcher data goes through a keyword-only parameter and never collides with a right. [test_membership_triggers.py]
- `demote()` drops an administrator to plain member, clears rights and custom title, keeps the tag. It refuses a non-administrator as a setup gap and changes nothing. [test_restricted_membership.py]
- `promote()` / `demote()` on the owner is a setup gap carrying `can't remove chat owner`; the owner is unchanged. [test_membership_triggers.py]
- A banned user's `join()`, `leave()`, `request_join()` are setup gaps until the ban ends. A ban drops the user's pending join request. [test_actor_alignment.py]
- `join()` by an administrator or owner already present keeps their status and rights. [test_actor_alignment.py]

### Other bots and anonymous administrators

- Another bot's actor produces messages and service messages with `is_bot` set and is held to a user actor's rights checks. [test_other_actors.py]
- A trigger only a person can produce is a setup gap for another bot: click, `pay()`, `inline_query()`, `chosen_inline_result()`, `vote()`, `pre_checkout_query()`, `shipping_query()`, `purchase_paid_media()`, `boost()`, `remove_boost()`, `update_subscription()`, `follow_deep_link()`. Nothing is fed or recorded. [test_other_actors.py]
- In a group, another bot's message or edit is delivered only when: either bot has bot-to-bot mode on and the message names the bot in a command or replies to the bot's message; or the bot has the mode on and is an administrator or has Group Privacy off. Otherwise it is stored, not fed, and the trigger returns `Withheld`. [test_other_actors.py]
- The implicit reply to a topic root does not count as a reply for that rule. [test_other_actors.py]
- In private, another bot's message is a setup gap unless both bots have the mode on. In a business chat it needs only the sender's mode, then is delivered. [test_other_actors.py]
- A service message another bot causes is delivered unless `deliver_service_messages_from_bots=False`; then it is stored and withheld. Service-ness is decided by content, so `send(fields=...)` follows the same switch. [test_other_actors.py]
- `in_(chat, anonymous=True)` posts as the supergroup: every message, service message and membership update it causes is from `GroupAnonymousBot` (id 1087968824, first name `Group`, a bot), with the chat as `sender_chat`. [test_other_actors.py]
- An anonymous message (never a service message) carries the administrator's custom title as `author_signature`. [test_other_actors.py]
- Binding anonymously is a setup gap outside a supergroup or for anyone but the owner or an administrator with `is_anonymous`. Every trigger rechecks once, at start, before changing anything. [test_other_actors.py]
- Join, leave and request-join are setup gaps for an anonymous binding. [test_other_actors.py]
- An anonymous binding uses the user's rights; the bot-to-bot rule does not apply to it. Topics it opens count as opened by the user. [test_other_actors.py]
- An anonymous binding's `state()` uses `GroupAnonymousBot`'s FSM key. Its reactions and votes name the chat (`actor_chat` / `voter_chat`), no user, and are stored as the chat's. Voting in another chat's poll is a setup gap. Clicks and queries come from the user. [test_other_actors.py]

## Deep links

- `follow_deep_link()` needs a `url` button on a message the environment holds: a named one, or any in the actor's chat. A url no such message carries raises naming where it looked. [test_deep_links.py]
- Following replays a real tap: the user's private chat with the bot gets `/start` or `/start <payload>`, and the full pipeline runs. [test_deep_links.py]
- With no target, the newest followable link to this bot is chosen; unfollowable ones are skipped, and if none remain the failure names each url and why. [test_deep_links.py]
- The slot that names the bot depends on the link kind; `?attach=<bot>` names it by its parameter. Kinds that address no bot (boost, invite, message) never match. [test_deep_links.py]
- Every `t.me`, `telegram.me`, `tg://resolve` and other `tg://<host>` url is classified into a kind from core.telegram.org/api/links, one policy per kind. [test_deep_links.py]
- `start` is the only followable kind. A bare `t.me/<bot>` and a bare `?start=` are plain starts. [test_deep_links.py]
- A link to another bot is refused, never replayed against the bot under test. [test_deep_links.py]
- Every other documented kind is refused naming that kind and what a client does, on every spelling it has. It is never refused as another kind. [test_deep_links.py]
- An undocumented query parameter is refused as not simulated, never guessed. [test_deep_links.py]
- A non-empty `start` wins over any other parameter, in either order. An empty `start` beside another parameter does not; the link classifies as the other kind. [test_deep_links.py]
- Companion parameters (`startapp`, `startattach`, `text`) never outrank the format that carries them. Alone, they classify by their own format. [test_deep_links.py]
- `t.me/s/<name>` is a channel web preview, not a Mini App. `t.me/+<digits>` and `?phone=` are phone links, not invites. [test_deep_links.py]
- A `tg://` host other than `resolve` is always a Telegram link: its documented kind, else a service link. A url addressing no Telegram surface is refused as not a Telegram link. [test_deep_links.py]
- Refusals point at the modeling trigger: invoice links at `pay()` / `pre_checkout_query()`, boost links at `boost()`, prefilled-draft links name the text and point at `send()`. [test_deep_links.py]
- A `start` payload must match `[A-Za-z0-9_-]{1,64}` or it is refused naming the rule. Opting out replays it verbatim and never makes another kind followable. [test_deep_links.py]

## Fake API: modeled vs record-only and result synthesis

- Every Bot API call a handler makes is intercepted. [test_session.py]
- The modeled surface covers at least: sends of messages, media, invoices, games, paid media, checklists, live photos and rich messages; edits of text, caption, markup, media, live location and checklist; deletes; single and batch forward/copy; pin/unpin/unpin-all; callback answers; member administration. [test_modeling.py]
- Every message-producing method stores its message with a unique `message_id` and returns that stored object. Its buttons are clickable like any other. [test_modeling.py]
- An unmodeled method succeeds by default: it is recorded and answered with a schema-valid result synthesized from generated method and type metadata. [test_synthesis.py]
- A newly generated Bot API method works without any toolkit change. [test_synthesis.py]
- The record-only surface is an enumerated list with a reason per entry. Deferred clusters are listed separately from refused ones. Docs show the same boundary. [test_record_only.py]
- The record-only list and the modeled registry never overlap. [test_record_only.py]
- Seeded answers come from the world: `sendChatAction` checks the chat exists, `getFile` echoes the `file_id`, `createInvoiceLink` is deterministic, `getUserPersonalChatMessages` reads the user's private chat. [test_message_methods.py]
- A stored message carries the scalar values its request stated, not substitutes. Media content stays synthesized. [test_modeling.py]
- A request field is never forced into a same-named payload field of another type. [test_modeling.py]
- Synthesized files get unique ids; a `file_id` the request passes is the stored one. [test_files.py]
- A dice carries its emoji (🎲 by default) and a value in its range. [test_fake_api_alignment.py]
- A synthesized enum-backed string takes a valid value. A synthesized bool is false; an empty-list count is zero. A sticker is never both animated and video. [test_fake_api_alignment.py]
- Every rich media block converts. [test_rich_messages.py]
- Every modeled call applies its parse mode (own or bot default) to every text it formats, nested items included. The world stores plain text plus entities, UTF-16 offsets. `HTML`, `MarkdownV2`, `Markdown` parse as TDLib does. [test_markup.py]
- Unparseable markup fails with `Bad Request: can't parse entities: ` plus TDLib's description and stores nothing. A number TDLib cannot read is no number, never a toolkit crash. [test_markup.py]
- Parsed text is trimmed at the end, and of leading spaces/newlines up to the first entity. [test_markup.py]
- A parse mode on a non-empty text beats explicit entities. Entities stand only with no parse mode or `none`. An unknown parse mode fails with `unsupported parse_mode`. [test_markup.py]
- An empty text fails with `message text is empty` before the chat is checked. A blank text (as sent or after parsing) fails with `text must be non-empty` after the chat and thread checks. A caption or other optional text that parses to nothing is cleared. [test_markup.py]

## Object identity and binding to the bot

- Every object the world hands out is bound to a `Bot` like a parsed response: nested objects and list items included; modeled, synthesized and overridden results alike; objects read straight from the world too. [test_mounting.py]
- An object already bound to a bot is never re-bound. A second `Bot` on the same session never takes over the world's objects; objects minted for its call are bound to it. [test_mounting.py]
- An update reaches the dispatcher already bound, so the handler gets the very object the chat stores. [test_mounting.py]
- An update carrying another environment's objects is copied, not claimed, and its message is registered in the destination chat. A reply never reuses the incoming message's id. [test_environment.py]
- A carried message whose id is taken by a different message raises `WorldLookupError` naming both. An equal message under the same id is a silent no-op. [test_environment.py]
- A chat's messages stay in ascending `message_id` order. A carried message keeps the id it arrived with. [test_environment.py]
- Values passed into a call are copied before they reach the world. A shared constant is never mutated, bound, or retained. [test_mounting.py]
- Stored value objects are copied on the way out. A `Message` is not: the returned message is the stored one. [test_mounting.py]
- A declared override result is answered with a fresh copy per call and is never mutated or bound. [test_overrides.py]
- A value already bound to this environment's bot is passed through by identity, on every entry path (trigger fields and edit changes alike). A value from another environment is copied. [test_mounting.py]

## Errors: setup gaps vs Telegram rejections, codes over texts

- A Telegram rejection fails as in production: the framework's own exception type, raised through the session's response check, from modeling rules, overrides and invalid operations alike. [test_errors.py]
- The dispatcher's error handlers receive it; a handler's own `except` catches it. [test_errors.py]
- Anything the blueprint never declared, or a surface the toolkit does not model, is a setup gap. It propagates out of the bot's call and fails the test; the bot's `except TelegramBadRequest` cannot swallow it. Its message says what to declare. [test_errors.py]
- An undeclared chat named by an outbound call is a setup gap, never "chat not found". The message lists the declared chats (type and name), points at the declaration and the on-demand helper, and names the override that gives the real refusal. [test_modeling.py]
- A declared user whose private chat was never opened gets a message saying a bot cannot write first. The bot's own calls never open a private chat. [test_modeling.py]
- Inline messages (`inline_message_id`) are unmodeled: every edit naming one is a setup gap. [test_modeling.py]
- A test reaching into the world directly (no call) gets `ApiRejection` unconverted. [test_errors.py]
- Every rejection carries an `error_code` and the matching type: 400 `TelegramBadRequest`, 403 `TelegramForbiddenError`, 429 `TelegramRetryAfter` with `retry_after`. [test_rejections.py]
- A rejection with 429 and no `retry_after`, or `retry_after` with another code, raises `ValueError` when built. [test_rejections.py]
- Descriptions are aids, not contracts. Every rejection is declared once in `aiogram.test.rejections`, never built from a literal elsewhere. [test_rejections.py]
- A sourced rejection reproduces its description verbatim (Bot API server, TDLib, core.telegram.org error lists); the read date is `SOURCES_CHECKED`. A best-effort one approximates. [test_rejections.py]
- `rejection_of()` names the declared rejection behind an exception; `rejection_fields()` gives what filled its description. Own exceptions match by identity, others by description. A flood is named through aiogram's rewording. [test_rejections.py]
- `perturb_rejection_descriptions=True` (fixture `bot_env_perturb_rejection_descriptions`) rewrites every description with a stable marker while keeping code, type and `retry_after`. A block declared without a message is perturbed too; a message the test declares is not. `rejection_of()` still works. [test_rejections.py]
- `raises()` takes an exception class or instance. A class needing more than method and message (`TelegramRetryAfter`, `TelegramMigrateToChat`) raises `TypeError` at declaration, naming what it needs and showing the instance to build. A non-Telegram value raises `TypeError`. [test_raises_validation.py]

## Overrides and call log

- An override beats both modeling and synthesis, for that test only. It returns a result or raises a Telegram error; a raised error leaves world state unchanged. [test_overrides.py]
- Overrides can be limited to a number of calls, so consecutive calls see outcomes in declared order. [test_overrides.py]
- An override can be narrowed by field equality on the resolved method (after defaults) plus a predicate, all ANDed. [test_overrides.py]
- A filter on a field the method lacks raises at declaration, naming the real fields. [test_overrides.py]
- Rules are tried in declaration order; the first that accepts wins. A rule that does not accept a call keeps its budget. [test_overrides.py]
- Every declaration returns a handle that withdraws exactly its own rules and works as a context manager. [test_overrides.py]
- Chat-addressing fields are resolved through the world before comparison, so an id rule matches an `@username` call and vice versa. [test_overrides.py]
- `env.blocked(...)` makes every call addressed at one party fail like a real block, with no call budget, under the same handle rules. [test_overrides.py]
- The block covers every delivery into that chat and every act on content already there: edit, pin/unpin, set and clear reaction. [test_overrides.py]
- The block matches the party by whichever field addresses it, but only an addressee field. A call into a reachable chat that merely mentions the blocked user succeeds. [test_overrides.py]
- Methods the block deliberately excludes are documented with a reason and succeed under it. [test_overrides.py]
- A call is logged before any override is consulted, so a refused call is still in the log as the bot built it. [test_overrides.py]
- `assert_overrides_consumed()` fails naming each declared expectation that never answered a call. Wait timeouts append the same list. [test_overrides.py]
- Rules generated as alternatives of a simulation (the block's methods) are never reported as unfired; hand-declared expectations beside them still are. [test_overrides.py]
- The call log records every intercepted call in order as the actual `TelegramMethod` objects, defaults resolved. It offers last-of-type, all-of-type, count and predicate filtering. [test_calls.py]
- The log keeps the call as the bot made it: text and `parse_mode` as passed, values as passed rather than the world's copies. [test_markup.py]

## Waiting

- `wait_for` re-checks a condition (sync or awaitable), yielding to the loop between checks, and returns the truthy value found. [test_waiting.py]
- An already-true condition returns without yielding first. [test_waiting.py]
- A wait never overshoots its timeout, whatever the poll interval. [test_waiting.py]
- The description is the second positional parameter (also accepted by keyword). Timing parameters are keyword-only. This holds for condition, chat, topic and broadcast waits. [test_waiting.py]
- Every wait that gives up raises `WaitTimeoutError`, a `TimeoutError`, naming what was awaited and showing what was there instead. [test_waiting.py]
- `watch=` takes one view or an iterable, mixed freely: declaration, chat/topic state, a user (their private chat, opened on demand) or a bare chat id. A timeout appends the watched views' contents and the unfired overrides. [test_waiting.py]
- A chat's message wait and a topic's message wait match every held message, not only new ones. A topic wait ignores sibling topics. No predicate matches any message. [test_waiting.py]
- Among several matches the highest `message_id` wins. [test_waiting.py]
- A predicate that raises counts as no match. On timeout the failure reports the exception type, its text and the message it hit. [test_waiting.py]
- `wait_for_message_in` returns once every named view holds a match, keyed by chat id, with the newest-match rule. It takes the `watch=` vocabulary, topics included. A timeout names only the views still missing, with per-view predicate errors. [test_waiting.py]
- One `default_wait_timeout` reaches every wait the environment owns, including chats added later. A per-call timeout wins. Default is 5 seconds. [test_waiting.py]
- A chat wait can take a receiver and wait among the bot's ephemeral messages to them. A shared-history wait that times out says when ephemeral messages were sent. [test_ephemeral_messages.py]

## Background tasks and draining

- A task counts as the bot's if it is alive or failed unseen, was not alive at the environment's first async entry, and is neither the caller nor a task waiting on the caller (awaiting it, via `gather`, or having created it). [test_wait_for_background_tasks.py]
- "Already alive" is fixed at the environment's first async action when construction ran with no loop, so a wider-scoped fixture's task is spared. An environment that never acted asynchronously owns no task. [test_environment.py]
- A task that made the environment's first call counts as the bot's. `drain()` and `wait_for_background_tasks()` count the same set. [test_wait_for_background_tasks.py]
- `wait_for_background_tasks()` cancels nothing, waits for tasks created meanwhile too, and returns how many it waited for. [test_wait_for_background_tasks.py]
- Its timeout defaults to the environment's wait timeout. On timeout it raises `WaitTimeoutError` naming each running task and coroutine, and leaves them running. [test_wait_for_background_tasks.py]
- A task that failed with an exception nobody retrieved raises `BackgroundTaskError` (base of `DrainedTaskError`), the first failure chained as cause. [test_wait_for_background_tasks.py]
- `drain()` is explicit and opt-in. It cancels and awaits the bot's tasks and returns how many it cancelled. [test_environment.py]
- A task that outlives its cancellation past the timeout makes `drain()` raise, naming it. [test_environment.py]
- A task that ended with its own failure (before or during the drain) makes `drain()` raise, naming it and keeping the original. A task that died earlier is not counted. [test_environment.py]
- When both kinds occur, the unfinished task is the error raised, naming the other, with the preserved failure attached. [test_environment.py]
- Only unretrieved failures are reported. A failure the bot retrieved, however late, is never reported. [test_task_pruning.py]
- Tasks are tracked weakly. A task that succeeded or was cancelled is not held once done. A failed task is held until its exception is retrieved; retrieved ones are released at the next count. [test_task_pruning.py]

## Routing diagnostics

- A route record says whether the dispatcher considered the update handled (anything but "unhandled"), which handler and router won, and the first exception in the middleware chain or handler, captured where raised even if swallowed later. [test_route_diagnostics.py]
- Whether a handler actually ran is the winning-handler field, not `handled`. A middleware that never calls next is handled with no handler. [test_route_diagnostics.py]
- A handler that raised `SkipHandler` is never reported as the winner, and its `SkipHandler` is not recorded as an error. [test_actor_alignment.py]
- Records are grouped per trigger scope. A trigger feeding several updates is one scope. A test can open a scope around several triggers. A lone feed opens its own. [test_route_diagnostics.py]
- A scope belongs to the task and the environment that opened it. A feed from another task or another environment never joins it; concurrent scopes never share or erase records. [test_route_diagnostics.py]
- Outside any scope, the last finished scope is reported. An update routed without the environment becomes its own finished scope. [test_route_diagnostics.py]
- `routes` lists the scope's records in the order routing finished. Before any feed it is empty and `last_route` is `None`. [test_route_diagnostics.py]
- The most relevant record is the newest with an exception, else the newest handled, else the newest. [test_route_diagnostics.py]
- `assert_handled_by` matches a substring of the winner's qualified name across every record of the scope, and on failure names where each record went, exceptions included. [test_route_diagnostics.py]
- `all_routes` keeps every record for the environment's life. [test_all_routes.py]
- `assert_updates_handled()` fails on every trigger none of whose updates was handled and on every update that raised (even if swallowed), each with its description, except triggers passed to `assert_unhandled()`. [test_all_routes.py]
- `assert_unhandled()` applies to the trigger `routes` reports, fails if it has nothing to flag, and returns what it would flag. [test_all_routes.py]

## FSM

- `env.state(user, chat)` resolves through the dispatcher's `FSMStrategy` and accepts topic and business connection, giving the same key the dispatcher used under every strategy. [test_fsm_keys.py]
- A test can set state and data before a trigger; handlers and scenes see it. [test_fsm_keys.py]

## Messages

- Sending appends a bot-sent message with a unique id and the resolved text. Bot defaults are applied before recording and storing. [test_modeling.py]
- Editing mutates the stored message in place and adds none. Deleting removes it; a later edit fails as Telegram would. [test_modeling.py]
- Media, live-location and checklist edits mutate in place; `stopMessageLiveLocation` returns the stored message. Unknown or deleted targets are `TelegramBadRequest`; inline targets are setup gaps. [test_message_methods.py]
- `editMessageText` fails on a message with no text or rich content; `editMessageCaption` fails on a message with no captionable media. [test_fake_api_alignment.py]
- The bot edits only what Telegram allows: not another sender's message outside a channel or business chat, not a customer's business message, not a forward, not a business message without its connection or a plain one with one. [test_fake_api_alignment.py]
- Every edit sets `edit_date`. [test_fake_api_alignment.py]
- Batch forward/copy append one message per source and return ids that exist in the target. A forward carries origin; a copy does not. An undeclared source chat is a setup gap. [test_message_methods.py]
- A copy or forward lands in the thread the request names, or none. A copy carries the new caption with its own entities, drops the caption on request, and stores the request's keyboard. [test_fake_api_alignment.py]
- Service, invoice, paid-media and giveaway messages are not copied; protected and service messages are not forwarded. A single call fails; a batch skips them. [test_fake_api_alignment.py]
- A copy or forward is the bot's own new message: no reply, edit date, protection, business connection, album, sender chat or sending details from the original; only the request's keyboard. [test_fake_api_alignment.py]
- A forward of a forward keeps the first origin. A copied poll is its own poll. [test_fake_api_alignment.py]
- `sendMediaGroup` stores one message per item with its media, caption and entities under one `media_group_id`; fewer than 2 or more than 10 items is rejected. [test_fake_api_alignment.py]
- A reply looks its target up in the chat the reply parameters name, else the target chat. Same chat sets `reply_to_message`; another chat sets `external_reply`. A missing target is rejected unless `allow_sending_without_reply`. [test_fake_api_alignment.py]
- `pinChatMessage` posts one `pinned_message` service message per pin, in the pinned message's topic, carrying the message without its own reply. [test_fake_api_alignment.py]
- `unpinChatMessage` without an id unpins only the newest pinned message. `unpinAllChatMessages` clears the pinned list. [test_message_methods.py]
- In a channel, every bot post (copies, forwards, service messages included) has the channel as `sender_chat` and no `from_user`. [test_fake_api_alignment.py]
- A checklist is stored with the title and tasks its request stated. [test_fake_api_alignment.py]
- Message 1 of a supergroup or channel is reserved for chat creation; a basic group's first message is 1. [test_forum_rules.py]

## Rich and ephemeral messages

- A stored rich message (sent, edited, copied, forwarded) carries the request's blocks and settings in Telegram's returned shape. Block media is synthesized as for the matching send. Unset required fields get valid values. `html`/`markdown`-only content is not parsed into blocks. [test_rich_messages.py]
- `editMessageText` replaces either kind of content with the other; a message never holds both. Markup follows the request; editing only markup keeps rich content. [test_rich_messages.py]
- Deep-link following and the misdirected-click hint cover rich buttons. [test_rich_messages.py]
- An ephemeral send returns `message_id` 0, an `ephemeral_message_id` and `receiver_user`, the deprecated `receiver_user_id` included. [test_ephemeral_messages.py]
- Ephemeral messages stay out of the shared history and its waits, are readable per receiver in send order, and keep their topic thread. [test_ephemeral_messages.py]
- An ephemeral send outside a group/supergroup is a Telegram rejection; to an undeclared receiver it is a setup gap. Nothing is stored. [test_ephemeral_messages.py]
- Only the receiver can click an ephemeral button, and its buttons are searched first. A miss names the receiver. The callback query carries the ephemeral message. [test_ephemeral_messages.py]
- A callback answer cannot replace an ephemeral message. [test_ephemeral_messages.py]
- Ephemeral edit methods change the stored ephemeral message by chat, receiver and ephemeral id; ephemeral delete removes it; a wrong receiver or unknown id is rejected. Regular edit and delete never reach ephemeral messages. [test_ephemeral_messages.py]
- An actor can send an ephemeral command in a group or supergroup only (else a setup gap): id 0, own ephemeral id, out of the shared history. [test_ephemeral_messages.py]
- A bot reply to an ephemeral command must itself be ephemeral and name an incoming ephemeral message of that chat; it has no `reply_to_message`. `message.reply()` produces that. [test_ephemeral_messages.py]
- A reply to an ephemeral command more than 15 seconds old is rejected. [test_time.py]

## Membership, rights and administration

- `getChatAdministrators` and `getChatMemberCount` derive from stored members. Other bots are omitted unless `return_bots`. An undeclared chat is a setup gap. [test_chat_administration.py]
- Title, description, permissions, sticker set and photo deletion change world state that `getChat` reports, per chat. A private chat rejects them. An undeclared chat is a setup gap. [test_chat_administration.py]
- Administrative actions post the service messages Telegram posts (`new_chat_title`, `delete_chat_photo`, ...). [test_chat_administration.py]
- A custom title belongs to an administrator and a tag to a regular member; the wrong one is rejected. `getChatMember` reports both. Losing admin status drops the title; a tag survives every status change. [test_chat_administration.py]
- `promoteChatMember` stores the whole rights mask; a later promotion replaces it, never unions. [test_chat_administration.py]
- A promotion with no true right demotes; any true right, `is_anonymous` alone included, keeps admin status. [test_chat_administration.py]
- A demotion clears the custom title and keeps the tag. [test_chat_administration.py]
- `restrictChatMember` clears admin rights. [test_chat_administration.py]
- `restrictChatMember` and `setChatPermissions` store what the request grants, applying Bot API couplings unless `use_independent_chat_permissions`: other kinds or previews grant every message kind; polls grant messages. [test_chat_administration.py]
- An unset permission follows the one the Bot API says it defaults to. The caller's permissions object is neither mutated nor kept. [test_chat_administration.py]
- Rights read back per chat type: a right that type does not report is unset; one it reports is a plain bool even if never stated. [test_chat_administration.py]
- Promoting, demoting, banning or restricting the owner fails with `can't remove chat owner`. [test_chat_administration.py]
- An administrator the bot promoted reports `can_be_edited` true; others false. [test_fake_api_alignment.py]
- A restricted user reports `is_member` for presence and counts as a member only while present. Restricting an absent user leaves them absent. Leaving or rejoining keeps the restriction and changes only `is_member`, in reads and updates. [test_restricted_membership.py]
- Granting every permission lifts a restriction: member if present, left otherwise, with no stored permissions or end date. [test_restricted_membership.py]
- A restriction or ban with no end reports `until_date` as the epoch (`0`). Any other status clears the end date. A basic-group ban has no end. [test_restricted_membership.py]
- `unbanChatMember` leaves the user absent and free to join, removing a present member by default. With `only_if_banned` it acts only on a banned user. [test_restricted_membership.py]
- Join requests are world state. `approveChatJoinRequest` adds the member and clears the request; `declineChatJoinRequest` only clears it; either on no pending request is rejected. [test_chat_administration.py]
- The bot's own profile (commands, name, description, short description, default admin rights, menu buttons) is world state, keyed by scope and language where the API keys it, declarable, copied per environment. [test_bot_profile.py]
- Profile setters and getters round-trip per scope and language. Commands do not fall back across languages; localized texts fall back to the default language, and clearing one restores the fallback. A per-chat menu button overrides the default. [test_bot_profile.py]
- Unset profile values return documented defaults: `[]`, `""`, `MenuButtonDefault`, all-`False` rights, the bot's first name. [test_bot_profile.py]

## Bot's own rights enforcement

- Unless `enforce_bot_rights=False`, every bot call into a group, supergroup or channel that its standing does not allow fails with Telegram's wording. [test_bot_rights.py]
- The rules are one table from method type to required right, consulted once per call, record-only methods included. [test_bot_rights.py]
- With `enforce_bot_rights=False` the bot holds every right. Private chats and user actors are never checked. [test_bot_rights.py]
- Pin/unpin: `can_pin_messages`, or `can_edit_messages` in a channel. Ban/unban/restrict members and sender chats and set permissions: `can_restrict_members`. Promote: `can_promote_members`. [test_bot_rights.py]
- Title, description, photo, sticker set: `can_change_info`. Member tag: `can_manage_tags`. Suggested posts: `can_post_messages`. Invite links and join requests: `can_invite_users`. [test_bot_rights.py]
- Unban and promote in a basic group fail with `method is available only in supergroup and channel chats` before rights are read. Touching the owner fails with `can't remove chat owner` before rights are read. [test_bot_rights.py]
- Topic methods check rights only for a topic that exists; a missing or deleted topic gets the topic's own refusal. [test_bot_rights.py]
- Creating a topic, and editing/closing/reopening a topic the bot did not create, and every General-topic method except unpinning, need `can_manage_topics`. Deleting another's topic needs `can_delete_messages`. [test_bot_rights.py]
- Deleting someone else's message needs admin status in a basic group, `can_delete_messages` elsewhere. [test_bot_rights.py]
- A non-admin bot's send, copy or forward needs the chat permission for that content kind, narrowed by its own restriction. A live location is checked as one. Paid media is checked only on forward/copy and needs both `can_send_photos` and `can_send_videos`. [test_bot_rights.py]
- Posting into a channel needs `can_post_messages`. [test_bot_rights.py]
- The owner holds every right. Chat permissions never grant an administrator right. [test_bot_rights.py]
- A bot that left or was kicked is refused every checked call and every send with `TelegramForbiddenError` and the server's text (e.g. `Forbidden: bot was kicked from the supergroup chat`), storing nothing. A kicked bot's blank text gets the 403, not the blank-text error. [test_bot_rights.py]
- Business-connection bot rights (gifts, stars) are declared but not enforced; a test needing the refusal declares an override. [test_stars_and_gifts.py]

## Forum topics

- Each topic owns its thread; the chat still lists every message. The world tracks name, icon and open/closed state. [test_topics.py]
- Create, edit, close, reopen, delete, unpin-all and the General variants are modeled and post the service message Telegram posts. [test_topics.py]
- Closing and reopening General post `forum_topic_closed` / `forum_topic_reopened` with no thread id. [test_topics.py]
- Hiding General also closes it; reopening General also unhides it. `editForumTopic` with an empty name keeps the name; an empty custom emoji id removes the icon. [test_fake_api_alignment.py]
- A private chat takes create, edit, delete, rename General and unpin; its topic messages carry their thread id. Close, reopen and hide fail with `the chat is not a supergroup forum`. No call reports a private chat's `is_forum`. [test_topics.py]
- A send, copy or forward into a thread the chat lacks, a deleted topic, or thread 1 of a forum supergroup fails with `message thread not found`. The topic is looked up after standing and before the replied message. [test_forum_rules.py]
- A forum method on a deleted topic fails with `TOPIC_DELETED`; on a thread that never existed, with `message thread not found`. [test_topics.py]
- A topic a test or actor names that the chat lacks is a setup gap naming the chat's topics. An actor bound to a since-deleted topic is a setup gap saying so. [test_forum_rules.py]
- A bot send, copy or forward into a closed topic, or into General while closed or hidden, fails with `TOPIC_CLOSED` unless the bot is owner, holds `can_manage_topics`, or created the topic. A refused message consumes no id. User actors are never refused. [test_forum_rules.py]
- A message in a supergroup topic other than General that replies to nothing in its chat replies to the topic's `forum_topic_created` and is a topic message. This covers bot sends, copies, forwards, topic service messages and actor messages. [test_forum_rules.py]
- An explicit reply keeps its target; a reply into another chat still carries the root. A replied-to message carries no reply of its own. [test_forum_rules.py]
- General and private-chat topics give no implicit reply. [test_forum_rules.py]
- A topic declared with `creator=` stores it, has its `forum_topic_created` from them, and gives the creator's exemptions (the bot: from `TOPIC_CLOSED` and `can_manage_topics` on its topic; a user: from `can_manage_topics`). Without `creator=` it is no one's and its service message is from the bot. [test_topic_creators.py]
- A user actor can create, close, reopen and delete topics, hide/unhide General, and close/reopen General, through the same code the bot methods use. [test_user_topic_actions.py]
- Each actor topic action stores and feeds Telegram's service message from that user. Deleting feeds nothing. [test_user_topic_actions.py]
- An actor names a topic by declaration, state or thread id, defaulting to its bound topic. [test_user_topic_actions.py]
- An actor topic action needs `can_manage_topics` (owner, or admin granted it) regardless of `enforce_bot_rights`, else a setup gap naming the right and how to grant it, changing nothing. [test_user_topic_actions.py]
- For creating a topic, the chat permission `can_manage_topics` stands in for the right, binding admins and members alike and narrowed by the actor's restriction. A topic's creator closes, reopens and deletes it without the right. [test_user_topic_actions.py]
- Only a supergroup's owner can turn topics off and on (else a setup gap); no update is delivered. Topics survive being off and return as they were. [test_forum_rules.py]
- While topics are off, forum methods fail with `the chat is not a forum`, and a bot send with a thread id is stored without one. [test_forum_rules.py]

## Polls and reactions

- A sent poll is stored on its message with question, options, type, anonymity, multiple-answer flag, correct answers, explanation, votes, closed state and close moment. A blueprint can declare one. [test_polls_and_reactions.py]
- A poll keeps all its correct option ids and allows revoting by default unless it is a quiz. A quiz with no correct ids is rejected. `stopPoll` stores the keyboard it is given. [test_fake_api_alignment.py]
- Voting feeds `poll_answer` and updates counts; counts always equal recorded voters, retractions included. An anonymous poll can also be fed as a `poll` update. [test_polls_and_reactions.py]
- Voting is a setup gap for an option that does not exist, several options on a single-answer poll, a changed vote where revoting is off, or a closed poll. [test_actor_alignment.py]
- `stopPoll` closes the stored poll and returns it with final counts. An unknown message, a message with no poll, or a closed poll is rejected. [test_polls_and_reactions.py]
- Reactions are stored per user, exposed through the chat (no message field carries them). [test_polls_and_reactions.py]
- `setMessageReaction` replaces the bot's reaction. `deleteMessageReaction` removes one user's reaction on one message. `deleteAllMessageReactions` removes one actor's reactions chat-wide. Unknown or deleted messages are rejected by the message-scoped methods. [test_polls_and_reactions.py]
- A reaction trigger derives `old_reaction` / `new_reaction` from stored state; removing one sends an empty `new_reaction`. `message_reaction_count` is triggerable. [test_polls_and_reactions.py]

## Invite links

- A chat stores its invite links with URL, creator, name, expiry, member limit, join-request flag, subscription period and price, and revoked state. Blueprints can declare them; each environment gets a copy. [test_invite_links.py]
- Create, create-subscription, edit, edit-subscription and revoke act on stored links. Edit and revoke return the stored link mutated, never a new object. [test_invite_links.py]
- Editing a subscription link keeps its period and price. An unknown link is rejected. A subscription period other than the permitted one is rejected. [test_invite_links.py]
- `exportChatInviteLink` replaces the primary link and revokes the previous one. Revoking the primary generates a replacement. `getChat` reports the current primary. [test_invite_links.py]

## Business connections and communities

- A blueprint declares business connections (owner, chat id, enabled, rights). `getBusinessConnection` reads them; an undeclared one is a setup gap. [test_business.py]
- `readBusinessMessage` and `deleteBusinessMessages` are modeled. [test_business.py]
- A message sent with a business connection id is stored as sent by the account owner, with the bot as sending business bot and the connection id on it. Without one it is the bot's. [test_business.py]
- Business message, edit, connection enabled/disabled and deleted-business-messages have triggers; the declared state follows them. [test_business.py]
- `deleteBusinessMessages` acts within one chat; ids from two chats are rejected and nothing is deleted. Business messages are numbered per connection. [test_fake_api_alignment.py]
- Editing a business message not sent by the bot and carrying no inline keyboard fails after 48 hours; this window binds every edit method. [test_time.py]
- A community can be declared with chats attached; full chat info carries it. Added-to and removed-from service messages are triggerable and stored; removal detaches the chat. [test_communities.py]

## Payments, Stars and gifts

- Callback, inline, shipping and pre-checkout queries are registered as outstanding. Answering one clears it; answering an unknown, expired or already-answered id is rejected. [test_modeling.py]
- A pre-checkout query expires 10 seconds after issue by the world clock; other queries never expire. [test_time.py]
- A full payment flow (shipping query, pre-checkout, `successful_payment`) is driven by triggers with answers validated against the registry. `ok=False` clears the query and produces no payment. [test_modeling.py]
- The star balance is derived from a transaction ledger plus the declared starting balance, never stored separately. [test_stars_and_gifts.py]
- A star transaction reports the charge id as its id, a positive amount, and the user as source (payment) or receiver (refund). [test_stars_and_gifts.py]
- `refundStarPayment` resolves a recorded charge, debits the balance and marks it refunded. A second refund is rejected; an unrecorded charge is a setup gap. [test_stars_and_gifts.py]
- `editUserStarSubscription` acts on the subscription behind a recorded charge; an unknown charge is a setup gap. [test_stars_and_gifts.py]
- `sendGift` creates an owned gift and spends its cost. The gift readers read that inventory; convert, upgrade and transfer move it. An unknown `owned_gift_id` is a setup gap. [test_stars_and_gifts.py]
- `getAvailableGifts` returns a stable catalogue. A gift id outside it is a setup gap listing the ids and naming the override. [test_stars_and_gifts.py]

## Sticker sets

- Sticker sets are held by name with title, type and stickers; declarable; copied per environment. [test_sticker_sets.py]
- Create, add, delete, replace, rename and delete-set are modeled and `getStickerSet` reports the result. [test_sticker_sets.py]
- A taken name and replacing a sticker the set lacks are Telegram rejections. An unknown set, or a sticker in no set, is a setup gap. [test_sticker_sets.py]
- `uploadStickerFile` returns a stable id usable by the set methods; `getCustomEmojiStickers` echoes its ids. Neither implies image data exists. [test_sticker_sets.py]
- Per-sticker attributes (emoji list, keywords, mask position, position) and set thumbnails are record-only. [test_sticker_sets.py]

## Files

- File content is declarable by id and served to the download helpers; `getFile` reports its size. Content is per environment. [test_files.py]
- Bytes uploaded inline are stored against the resulting file id, so upload-then-download reads back what was sent. Two uploads get distinct ids. [test_files.py]
- Downloading content the environment does not hold raises an error naming the file id and both remedies (declare content, override the call). It is never empty content and is not swallowed by `bot.download` / `bot.download_file`. [test_files.py]

## World time

- The clock starts at real time to the second, or at the given start, then stands still until advanced. The date of anything happening at present is the clock's time. [test_time.py]
- The clock never moves backwards; a negative advance fails and changes nothing. [test_time.py]
- `advance_time` dispatches the updates time causes before returning, ordered by moment then scheduling order, including events scheduled during the advance that fall before its target. [test_time.py]
- An advance cannot overlap itself: one from inside an advance or a concurrent task is a setup gap. [test_time.py]
- Bot-passed dates are read in whole seconds against the clock's whole second. [test_time.py]
- A duration `until_date` counts from the clock. Less than 30 seconds or more than 366 days ahead means forever. Once reached, every read sees the restriction or ban ended. [test_time.py]
- A poll with an open period or close date (never both) closes when the clock reaches it, feeds a `poll` update, and refuses votes. A moment under 5 or over 2628000 seconds ahead is rejected. A poll stopped earlier does not close again. [test_time.py]
- Editing or stopping a live location fails after its period, after stop, or if never live, unless the period is forever (`0x7FFFFFFF`). A new non-forever period may not exceed the current by more than a day or end more than 90 days ahead. [test_time.py]
- Deleting a message 48 hours old or more is rejected; batch deletion skips it. A private-chat dice is deletable only after 24 hours. [test_time.py]
- The docs recipe for fast sleeps keeps real DB drivers and the loop's clock, explains the `looptime` clash, states the toolkit has no time-control mode, and runs as written. [test_sleep_scaling_recipe.py]

## Flood control

- With `rate_limits`, a message-producing call into a chat over a limit fails with 429 `Too Many Requests: retry after N` and `TelegramRetryAfter.retry_after` in whole seconds until allowed. Without it nothing is limited. [test_rate_limits.py]
- Default limits: one message per second per chat, and 20 per minute in a group or supergroup, counted across topics. [test_rate_limits.py]
- Limits are read after Telegram's own pre-send checks; a refused call changes nothing and is not counted. [test_rate_limits.py]
- Counted methods are the modeled sends from the registry. A success counts every message it stores (an album of ten counts ten). A call under a limit passes even if it takes the chat over. [test_rate_limits.py]
- The limiter reads the loop's clock plus what `advance_time` moved. [test_rate_limits.py]

## pytest plugin and fixtures

- The plugin loads through the `pytest11` entry point `aiogram`, which points at the shim `aiogram/test/_autoload.py`, not at the plugin (TW-188). `-p no:aiogram` turns it off. Enabling it explicitly as well (`-p aiogram.test.plugin` or `pytest_plugins`) loads it once. Before pytest 8 the shim registers nothing. [test_plugin.py]
- Importing `aiogram` or `aiogram.test` never imports pytest. [test_plugin.py]
- Fixtures: `bot_blueprint`, `bot_dispatcher`, `bot_env`, `bot_chat`, `bot_user`, plus value fixtures `bot_env_wait_timeout`, `bot_env_clock_start`, `bot_env_enforce_bot_rights`, `bot_env_rate_limits`, `bot_env_deliver_service_messages_from_bots`, `bot_env_perturb_rejection_descriptions`, `bot_env_assert_updates_handled`. [test_plugin.py]
- Value fixtures are overridable at any scope; `bot_env` and everything derived from it are function-scoped. [test_plugin.py]
- With no overrides, `bot_env` holds a default private chat, a default user and a bot identity. [test_plugin.py]
- `bot_env` builds the environment from what the value fixtures return; an explicit per-call timeout still wins. [test_plugin.py]
- `bot_env` is disposed after each test, passed or failed. [test_plugin.py]
- With `bot_env_assert_updates_handled` true, a passing test is checked in the call phase and fails if it left updates unhandled; a failed test is not checked; `assert_unhandled()` exempts. [test_plugin.py]
- Failing `==` on a `ChatState` lists the chat and its messages. Failing `==` on two `TelegramMethod`s names the methods and the differing fields. [test_plugin.py]
- Two `TelegramObject`s equal in payload but bound to different bots get an explanation naming each binding and pointing at `model_dump()` comparison. [test_plugin.py]
- The explanation never raises; a comparison it cannot serialize is left to pytest. [test_plugin.py]
- Everything fixtures give is reachable through public imports, and manual construction plus explicit disposal behaves identically. [test_plugin.py]
- The plugin imposes no asyncio plugin or loop policy; the project's own async setup is used, and the docs state what it needs. [test_plugin.py]

## Differences from the archived spec

- Plugin registration. The spec pointed the `pytest11` entry point straight at `aiogram.test.plugin`. It points at a shim instead (TW-188), so the explicit forms do not fail on double registration.
- Fixture set. The spec listed a fixture for "the bot". `aiogram/test/plugin.py` has no bot fixture; the bot is `bot_env.bot`. The plugin also has value fixtures the spec never mentions: `bot_env_clock_start`, `bot_env_enforce_bot_rights`, `bot_env_rate_limits`, `bot_env_deliver_service_messages_from_bots`. The spec covers `bot_env_perturb_rejection_descriptions` and `bot_env_assert_updates_handled` only in the environment spec.
- Undeclared chats. Several older requirements said an unknown chat raises `TelegramBadRequest`: batch forward/copy from an unknown chat, `sendChatAction`, administering a chat, `getChatMemberCount` / `getChatAdministrators`. The later setup-gap rule wins in code and tests (`test_message_methods.py`, `test_chat_administration.py`): all of these raise `WorldLookupError` ("not declared in the blueprint").
- Star/business rights. "Star rights are not enforced" said this matches "the toolkit not enforcing rights anywhere". The bot's own chat rights are enforced by default (`enforce_bot_rights=True`). Only business-connection rights are unenforced (docs/dispatcher/testing.rst).
- Owner via `promote()` / `demote()`. One scenario said the trigger "raises the same refusal `promoteChatMember` gives" and another said it is a setup gap. The code raises `WorldLookupError` carrying the `can't remove chat owner` text (`test_membership_triggers.py`).
