## ADDED Requirements

### Requirement: The bot's background tasks can be waited for

`wait_for_tasks()` SHALL wait, cancelling nothing, until every task the environment counts
as the bot's is done: those created since its first asynchronous entry, other than those
alive then, the caller, and the task that made that entry. A task created while waiting
SHALL be waited for too. A task that ended with an exception nobody retrieved SHALL be
raised as `BackgroundTaskError`, the base of `DrainedTaskError`, with the first chained as
its cause. At the timeout, which defaults to the environment's wait timeout, it SHALL raise
`WaitTimeoutError` naming each task still running and its coroutine, and leave them
running. It SHALL return how many tasks it waited for.

#### Scenario: A results broadcast

- **WHEN** a handler broadcasts from a task and the test waits for the bot's tasks
- **THEN** every message of the broadcast is stored, and the task was not cancelled

#### Scenario: A task that never ends

- **WHEN** the bot's task is still running at the timeout
- **THEN** `WaitTimeoutError` names it and its coroutine, and it keeps running

#### Scenario: A task that failed

- **WHEN** a bot's task raised an exception nobody retrieved
- **THEN** the wait raises `BackgroundTaskError` with that exception as its cause

### Requirement: Every route of a test is kept and can be checked

An environment SHALL keep the route record of every update it routed for its whole life,
readable as `route_history`. `assert_updates_handled()` SHALL fail on every trigger none of
whose updates was handled and on every update that raised, even if an error handler
swallowed it, listing each with its description, except for a trigger the test passed to
`expect_unhandled()`. `expect_unhandled()` SHALL apply to the trigger `routes` reports,
SHALL fail if that trigger has nothing the check would flag, and SHALL return what it would
flag. With the `bot_env_assert_updates_handled` fixture returning true, the plugin SHALL run
the check after each test that passed, failing that test.

#### Scenario: An update in the middle of a game went nowhere

- **WHEN** a test feeds a handled update, an unhandled one, and a handled one
- **THEN** `route_history` holds all three, and `assert_updates_handled()` fails naming the
  unhandled one

#### Scenario: A join whose service message nobody claims

- **WHEN** a trigger feeds a handled update and an unhandled one
- **THEN** `assert_updates_handled()` passes

#### Scenario: An update the test meant the bot to ignore

- **WHEN** a test calls `expect_unhandled()` after an unhandled trigger
- **THEN** `assert_updates_handled()` passes

#### Scenario: The plugin checks a passing test

- **WHEN** the fixture flag is on and a passing test left an update unhandled
- **THEN** that test fails, and a test that called `expect_unhandled()` passes

### Requirement: Parse modes are applied as the Bot API applies them

Every modeled call SHALL apply each parse mode it carries, its own or the bot's default,
to the text it formats, nested items included, and the world SHALL store the plain text with
the entities, offsets in UTF-16 code units. `HTML`, `MarkdownV2` and `Markdown` SHALL be
parsed as TDLib parses them. Markup that cannot be parsed SHALL fail the call with
`Bad Request: can't parse entities: ` and TDLib's description, and store nothing. A parse
mode on a non-empty text SHALL win over explicit entities, which SHALL stand only without a
parse mode or with `none`. An unknown parse mode SHALL fail with `unsupported parse_mode`.
The call log SHALL keep the call as the bot made it.

#### Scenario: A bold word

- **WHEN** a handler sends `<b>Night</b> falls` with `parse_mode="HTML"`
- **THEN** the chat stores `Night falls` with a bold entity at offset 0, length 5

#### Scenario: An unescaped less-than sign

- **WHEN** a handler sends `Score: 3 < 5` with `parse_mode="HTML"`
- **THEN** the call raises `TelegramBadRequest` with `Bad Request: can't parse entities:
  Unsupported start tag "" at byte offset 9`, and nothing is stored

#### Scenario: The bot's default parse mode

- **WHEN** the bot's default parse mode is `MarkdownV2` and a handler sends `*Day*`
- **THEN** the chat stores `Day` with a bold entity

#### Scenario: Entities and a parse mode together

- **WHEN** a handler passes both `entities` and `parse_mode="HTML"`
- **THEN** the stored entities are the parsed ones

### Requirement: The documentation shows fast sleeps that keep the loop's clock real

The documentation SHALL show how a suite that keeps real database drivers speeds up a bot's
own sleeps without replacing the event loop's clock, SHALL say why `looptime` and such
drivers clash, and SHALL say that the toolkit has no time control mode of its own. The code
it shows SHALL run as written.

#### Scenario: The recipe as written

- **WHEN** the recipe's code blocks are written into a project and its tests run
- **THEN** they pass, the fifteen-second pause takes under a second, and `asyncio.sleep`
  and the loop's clock are untouched

### Requirement: A group has the default permissions Telegram gives a new one

A group or a supergroup SHALL have, unless its declaration gives others, the permissions
Telegram gives a new one: every kind of message and reaction, and inviting users, allowed,
and changing the chat's info, pinning messages, creating topics and editing one's tag denied.
`getChat` SHALL report them, and the checks of what the bot may send as a plain or a
restricted member SHALL read the same value. A private chat and a channel SHALL have none.
`add_group` and `add_supergroup` SHALL accept `permissions=` to declare others, and
`default_chat_permissions()` SHALL return the default as a new object that the Bot API's
couplings leave unchanged.

#### Scenario: A new supergroup

- **WHEN** a test declares a supergroup and calls `getChat` on it
- **THEN** `permissions` is the default, and the bot as a plain member sends text, polls and
  dice into it

#### Scenario: Declared permissions replace the default

- **WHEN** a supergroup is declared with `permissions=` that deny polls
- **THEN** `getChat` reports them and the bot's `sendPoll` is refused as a plain member

### Requirement: Users and chats can be added to a running environment

A running environment SHALL be able to add a user, a private chat, a group, a supergroup and a
channel, with members, taking what the blueprint's methods of the same name take. They SHALL
be built by the same code as declared ones, so the shape is identical, and SHALL return the
handle `env.user()` or `env.chat()` returns. The id SHALL be the next free one unless given,
and an id already taken SHALL raise `ValueError`. Members SHALL be named by spec, by actor or
by id, and a user the world does not have SHALL raise `WorldLookupError` naming `add_user`.
The blueprint the environment was built from SHALL NOT change.

#### Scenario: A newcomer joins a new group

- **WHEN** a test adds a user and a supergroup with that user as a member, and the user sends
  a message into it
- **THEN** the dispatcher handles the message as it handles one in a declared chat

#### Scenario: A chat equals a declared one

- **WHEN** a supergroup is added with an id and the same one is declared in a blueprint with
  that id
- **THEN** the two chats are equal

#### Scenario: A shared blueprint

- **WHEN** two environments are built from one blueprint and one adds a user and a chat
- **THEN** the blueprint and the other environment are unchanged

### Requirement: A text an actor sends carries its bot commands

A text, and a caption, that a user actor sends or edits SHALL carry the `bot_command`
entities Telegram attaches, with UTF-16 offsets, unless the test passes `entities` or
`caption_entities` itself, even empty. A command SHALL be a slash at the start of the text or
after a character that is not a letter, a number, `_`, `/`, `<` or `>`, then one to 64 ASCII
letters, digits or underscores, then optionally `@` and three to 32 of them, and SHALL not be
followed by a letter, a number, `_`, `/`, `<` or `>`. A command that breaks a rule SHALL have
no entity, and neither SHALL the command before an `@name` that does. Messages the bot sends
SHALL not change.

#### Scenario: A command in the middle of a text

- **WHEN** an actor sends `hi /start@my_bot now`
- **THEN** the message carries one `bot_command` entity at offset 3 with length 13

#### Scenario: Not a command

- **WHEN** an actor sends `a/start`, `//start` or `/start/more`
- **THEN** the message carries no entity

#### Scenario: Entities passed by the test

- **WHEN** an actor sends `/start` with `fields={"entities": []}`
- **THEN** the message carries exactly the entities passed

### Requirement: Raising a Telegram exception from a class it cannot be built from is refused

`raises()` SHALL accept an exception class or an instance. A class whose constructor needs
more than the method and the message, such as `TelegramRetryAfter` and
`TelegramMigrateToChat`, SHALL raise `TypeError` when declared, naming what it needs and
showing the instance to build, and a value that is not a Telegram exception class or instance
SHALL raise `TypeError` too. A class that is built from the method and the message SHALL
still be accepted.

#### Scenario: The class of an exception that needs a retry time

- **WHEN** a test declares `raises(TelegramRetryAfter)`
- **THEN** `TypeError` names `retry_after` and shows `TelegramRetryAfter(method=...,
  message=..., retry_after=5)`, and nothing is declared

#### Scenario: A usual class

- **WHEN** a test declares `raises(TelegramForbiddenError, "Forbidden: x")`
- **THEN** the call fails with that exception and message

### Requirement: Finished tasks are not held for the life of the environment

The environment SHALL hold a task it tracked only while the task runs, and SHALL forget a task
that succeeded or was cancelled when it ends. A task that failed SHALL be kept until its
exception is retrieved, by the bot or by a report, so that `wait_for_tasks()` and `drain()`
still raise `BackgroundTaskError` and `DrainedTaskError` for a failure nobody retrieved, and
SHALL NOT for one the bot retrieved, however late. A disposed environment SHALL hold no task.

#### Scenario: Many short tasks

- **WHEN** the bot spawns two hundred tasks that each finish
- **THEN** the environment holds none of them, and none is kept alive by it

#### Scenario: A failure among them

- **WHEN** one of many finished tasks failed and nobody retrieved why
- **THEN** `wait_for_tasks()` raises `BackgroundTaskError` naming it, with its exception as the
  cause, and afterwards the environment holds nothing

#### Scenario: A failure the bot handled

- **WHEN** the bot awaits a task that failed, and catches the exception, at any later time
- **THEN** neither `wait_for_tasks()` nor `drain()` reports it

## RENAMED Requirements

- FROM: `### Requirement: A group has the default permissions Telegram gives a new one`
- TO: `### Requirement: A group grants its members every permission by default`

## MODIFIED Requirements

### Requirement: A group grants its members every permission by default

A group or a supergroup SHALL have, unless its declaration gives others, every member
permission granted. Telegram does not publish what a new group allows, so this SHALL be
documented as the toolkit's convention, with `permissions=` as the way to model a stricter
group. `getChat` SHALL report them, and the checks of what the bot may send as a plain or a
restricted member SHALL read the same value; they SHALL NOT grant the bot an
administrator's right. A private chat and a channel SHALL have none. `add_group` and
`add_supergroup` SHALL accept `permissions=` to declare others, and
`default_chat_permissions()` SHALL return the default as a new object that the Bot API's
couplings leave unchanged.

#### Scenario: A new supergroup

- **WHEN** a test declares a supergroup and calls `getChat` on it
- **THEN** `permissions` grants every permission, and the bot as a plain member sends text,
  polls and dice into it

#### Scenario: Declared permissions replace the default

- **WHEN** a supergroup is declared with `permissions=` that deny polls
- **THEN** `getChat` reports them and the bot's `sendPoll` is refused as a plain member

### Requirement: The bot's background tasks can be waited for

`wait_for_tasks()` SHALL wait, cancelling nothing, until every task the environment counts
as the bot's is done: those alive or failed unseen, other than those alive at its first
asynchronous entry, the caller, and every task waiting on the caller, by awaiting it,
directly or through `gather`, or by having created it. A task that made the environment's
first call SHALL count as the bot's. `drain()` SHALL count the same tasks. A task created
while waiting SHALL be waited for too. A task that ended with an exception nobody retrieved
SHALL be raised as `BackgroundTaskError`, the base of `DrainedTaskError`, with the first
chained as its cause. At the timeout, which defaults to the environment's wait timeout, it
SHALL raise `WaitTimeoutError` naming each task still running and its coroutine, and leave
them running. It SHALL return how many tasks it waited for.

#### Scenario: A results broadcast

- **WHEN** a handler broadcasts from a task and the test waits for the bot's tasks
- **THEN** every message of the broadcast is stored, and the task was not cancelled

#### Scenario: A worker that touched the environment first

- **WHEN** the test starts a worker that calls the bot first and then sleeps, and drains
- **THEN** the worker is cancelled and counted

#### Scenario: A drain from a child task

- **WHEN** the test awaits a child task that drains
- **THEN** the test's task is neither cancelled nor waited for

#### Scenario: A task that never ends

- **WHEN** the bot's task is still running at the timeout
- **THEN** `WaitTimeoutError` names it and its coroutine, and it keeps running

#### Scenario: A task that failed

- **WHEN** a bot's task raised an exception nobody retrieved
- **THEN** the wait raises `BackgroundTaskError` with that exception as its cause

### Requirement: Finished tasks are not held for the life of the environment

The environment SHALL note the tasks it tracks weakly, and SHALL keep no task that succeeded
or was cancelled once it ends. A task that failed SHALL be kept until its exception is
retrieved, by the bot or by a report, so that `wait_for_tasks()` and `drain()` still raise
`BackgroundTaskError` and `DrainedTaskError` for a failure nobody retrieved, and SHALL NOT
for one the bot retrieved, however late. Retrieved failures SHALL be let go when the tasks
are next counted rather than each time a task ends. A disposed environment SHALL hold no
task.

#### Scenario: Many short tasks

- **WHEN** the bot spawns two hundred tasks that each finish
- **THEN** the environment holds none of them, and none is kept alive by it

#### Scenario: A failure among them

- **WHEN** one of many finished tasks failed and nobody retrieved why
- **THEN** `wait_for_tasks()` raises `BackgroundTaskError` naming it, with its exception as the
  cause, and afterwards the environment holds nothing

#### Scenario: A failure the bot handled

- **WHEN** the bot awaits a task that failed, and catches the exception, at any later time
- **THEN** neither `wait_for_tasks()` nor `drain()` reports it

### Requirement: Parse modes are applied as the Bot API applies them

Every modeled call SHALL apply each parse mode it carries, its own or the bot's default,
to the text it formats, nested items included, and the world SHALL store the plain text with
the entities, offsets in UTF-16 code units. `HTML`, `MarkdownV2` and `Markdown` SHALL be
parsed as TDLib parses them. Markup that cannot be parsed SHALL fail the call with
`Bad Request: can't parse entities: ` and TDLib's description, and store nothing. A number
TDLib cannot read SHALL be no number, never a failure of the toolkit. A parsed text SHALL be
trimmed at its end, and of leading spaces and newlines up to its first entity. A parse mode
on a non-empty text SHALL win over explicit entities, which SHALL stand only without a parse
mode or with `none`. An unknown parse mode SHALL fail with `unsupported parse_mode`. A
message text that is empty SHALL fail with `message text is empty`, and one that is blank,
as sent or once parsed, with `text must be non-empty`; a caption that parses to nothing
SHALL be cleared. The call log SHALL keep the call as the bot made it.

#### Scenario: A bold word

- **WHEN** a handler sends `<b>Night</b> falls` with `parse_mode="HTML"`
- **THEN** the chat stores `Night falls` with a bold entity at offset 0, length 5

#### Scenario: An unescaped less-than sign

- **WHEN** a handler sends `Score: 3 < 5` with `parse_mode="HTML"`
- **THEN** the call raises `TelegramBadRequest` with `Bad Request: can't parse entities:
  Unsupported start tag "" at byte offset 9`, and nothing is stored

#### Scenario: A malformed user id

- **WHEN** a handler sends `<a href='tg://user?id=--5'>x</a>` with `parse_mode="HTML"`
- **THEN** the chat stores `x` with a text link, and nothing raises

#### Scenario: Markup that parses to nothing

- **WHEN** a handler sends `<b> </b>` with `parse_mode="HTML"`
- **THEN** the call raises `TelegramBadRequest` with `text must be non-empty`, and nothing
  is stored

#### Scenario: Leading whitespace

- **WHEN** a handler sends ` <b>a</b>` with `parse_mode="HTML"`
- **THEN** the chat stores `a` with a bold entity at offset 0

#### Scenario: The bot's default parse mode

- **WHEN** the bot's default parse mode is `MarkdownV2` and a handler sends `*Day*`
- **THEN** the chat stores `Day` with a bold entity

#### Scenario: Entities and a parse mode together

- **WHEN** a handler passes both `entities` and `parse_mode="HTML"`
- **THEN** the stored entities are the parsed ones

### Requirement: Users and chats can be added to a running environment

A running environment SHALL be able to add a user, a private chat, a group, a supergroup and a
channel, with members, taking what the blueprint's methods of the same name take. They SHALL
be those blueprint methods run on a scratch blueprint, so the signatures and the shape are
the same, and SHALL return the handle `env.user()` or `env.chat()` returns, a chat's live
state. The id SHALL be the next free one unless given, allocated by the one function the
blueprint uses with the ids the world has taken, and an id already taken SHALL raise
`ValueError`, in a blueprint as in a running world. Members SHALL be named by spec, by actor
or by id, in a blueprint as well, and a user the world does not have SHALL raise
`WorldLookupError` naming `add_user`. The blueprint the environment was built from SHALL NOT
change.

#### Scenario: A newcomer joins a new group

- **WHEN** a test adds a user and a supergroup with that user as a member, and the user sends
  a message into it
- **THEN** the dispatcher handles the message as it handles one in a declared chat

#### Scenario: A chat equals a declared one

- **WHEN** a supergroup is added with an id and the same one is declared in a blueprint with
  that id
- **THEN** the two chats are equal

#### Scenario: The same signature

- **WHEN** a test reads the signature of `env.add_supergroup`
- **THEN** its parameters are those of `Blueprint.add_supergroup`

#### Scenario: A shared blueprint

- **WHEN** two environments are built from one blueprint and one adds a user and a chat
- **THEN** the blueprint and the other environment are unchanged
