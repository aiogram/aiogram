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
