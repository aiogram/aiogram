## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`.

- `drain()` finds the bot's tasks as those created since the environment's first
  asynchronous entry, minus those alive then and minus the caller.
- Route records live in trigger frames; the environment keeps only the last finished one.
- `handle_call` resolves `Default` sentinels, so a call's `parse_mode` is already the bot's
  default when it is not given; the world stored `text` and `entities` as the call had them.

## Decisions

### D1. Waiting uses drain's set of tasks

`wait_for_tasks()` and `drain()` share `_own_tasks()`, so they agree on what is the bot's.
It also leaves out the task that made the first entry, normally the test's own: a wait or
a drain called from a child task would otherwise wait for, or cancel, the test awaiting
it. The wait repeats `asyncio.wait` on what is pending until nothing is, so a task spawned
meanwhile counts, against one deadline on the loop's clock. Failures are collected the way
`drain()` collects them and raised as `BackgroundTaskError`; `DrainedTaskError` became its
subclass so one `pytest.raises` catches both. A timeout names each task and its
coroutine's qualified name, chains the first failure if there is one, and cancels nothing.

### D2. The history keeps trigger frames

Every `_TriggerFrame` is appended to the environment's history when it opens, and so is the
frame a direct `feed_update` gets. `route_history` flattens them. Keeping frames rather
than records lets the check reason per trigger, as `assert_handled_by` does: a frame is
flagged whole when none of its records was handled, else only its records that raised. So
`member.join()`, whose service message nobody claims, passes, and a handler that raised is
caught even when another update of its trigger was handled. Every record is kept; a test's
worth of them is small.

`expect_unhandled()` marks the frame `routes` reads. It fails when that frame has nothing
to flag, so a stale call cannot hide a handled trigger, and returns what it would flag.
`assert_handled_by` needs no escape: a trigger it passes on has a handled update.

The plugin runs the check from a `pytest_runtest_call` wrapper, reading the fixture flag and
the environment from `item.funcargs`, so it fails the test rather than its teardown and is
skipped when the test already failed.

### D3. Parsing is a pass over the call, before the handler

`apply_parse_modes()` walks the resolved call and what it carries, and returns a copy whose
texts are plain. A field `parse_mode` formats `text`, `message_text`, `caption` or `title`;
`x_parse_mode` formats `x`; the entities are `x_entities`, else `entities`. That covers
every Bot API type with a parse mode without a table to keep. `handle_call` runs it for a
modeled method after overrides and before the flood check, as the Bot API server parses
before the request reaches Telegram. The call log keeps the call as made.

The rule for explicit entities is the server's `Client::get_formatted_text`: a parse mode
other than empty or `none` on a non-empty text is applied and the entities are dropped;
otherwise the entities stand. An unknown mode fails with its `Unsupported parse_mode`.

The parsers in `markup.py` are ports of TDLib's `parse_html`, `parse_markdown_v2` and
`parse_markdown` in `td/telegram/MessageEntity.cpp`, run over UTF-8 bytes so error offsets
are TDLib's byte offsets, counting UTF-16 units for entities. The error texts are TDLib's,
behind the `Can't parse entities: ` prefix its `parseTextEntities` adds, lowercased at the
first letter as the server relays them. Links follow `LinkManager::check_link` (an HTTP
link without a path gets `/`, a bad one drops its entity) and `get_link_user_id`; a mention
of an undeclared user is dropped, as TDLib skips a user it cannot reach.

After parsing, only part of TDLib's `fix_formatted_text` is modeled: `\r` and trailing
whitespace are removed, entities nested in code or pre are dropped, and entities are sorted
by offset, length and TDLib's type priority.

**Assumptions.** The refusals of a bad `<tg-time>` or `tg://time` link are worded by the
toolkit, after TDLib's custom emoji ones; TDLib's are not known. Nested items, such as a
media group's captions, fail with the same description as a top-level text.

aiogram's own renderers are the test oracle: text and entities rendered by
`html_decoration` or `markdown_decoration` must parse back unchanged. Two renderings fail
that against Telegram's grammar and are left out of it: HTML `pre` with a language, written
as a `language=` attribute instead of `class="language-..."`, and the MarkdownV2 custom
emoji link, written with `emoji_id=` instead of `id=`.

### D4. Fast sleeps are a recipe, not a mode

A time control mode would have to decide which timers are the bot's and which are a
driver's, and nothing in asyncio tells them apart. Until that is designed, the docs show
the seam that needs no such decision: the application's own pause helper, replaced in the
tests by one that sleeps a thousandth as long, with `asyncio.sleep` and the loop's clock
left alone. `test_sleep_scaling_recipe.py` reads the recipe's code blocks out of
`testing.rst`, writes them into a project and runs it, so the recipe cannot drift.

### D5. A group's permissions are Telegram's defaults, not nothing

`Blueprint.build` gives a group or a supergroup `default_chat_permissions()` when its
`ChatSpec.permissions` is `None`, and nothing to a private chat or a channel, so the
spec's field keeps meaning "unset" and a hand-built spec gets the same. The default is
built as `granted_permissions()` stores a request, so the couplings and defaults the Bot
API documents hold of it; `require_send_permission` and the restricted member's narrowing
read `ChatState.permissions` as before, which is now this value. The mask: every kind of
message, reaction and inviting allowed; changing info, pinning, creating topics and editing
a tag denied.

**Assumption.** Telegram's documentation does not list these defaults. They are what its
clients show for a new group and what `getChat` returns for one, as far as is known, and
the toolkit says so in its docs.

### D6. Additions are the blueprint's builders over a scratch blueprint

`Blueprint.build` was split: `chat_state()` and `user_state()` turn a declaration into
state, and `build` calls them. `BotTestEnvironment.add_*` declare on a scratch `Blueprint`
for the same bot, so the builders' defaults, the bot's membership and the permissions
default are the blueprint's, then turn the declaration into state with the same two
functions and register it. The environment's own blueprint is shared by tests at any scope,
so it is never written to.

Ids come from the blueprint's formulas, counting the world's users and chats, and skip
what is taken. Members are named by spec, actor or id and turned into declarations of the
world's users; the bot maps to the blueprint's own `bot`, so `bot_status=` and an entry for
it still conflict. A user the world lacks raises. Topics are left out: an owner's
`create_topic()` makes them, and `is_forum=True` turns them on.
