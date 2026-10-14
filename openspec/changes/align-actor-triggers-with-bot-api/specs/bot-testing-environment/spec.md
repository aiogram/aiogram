## ADDED Requirements

### Requirement: A click on a given message checks the stored button

A click trigger given a message SHALL resolve that message's stored version in the actor's
chat, and SHALL require the clicked `callback_data` to be on it, failing as a setup error
otherwise.

#### Scenario: A stale copy resolves to the stored message

- **WHEN** the bot edits a message after the test kept a copy, and the test clicks with the
  copy
- **THEN** the dispatched `callback_query` carries the stored, edited message

#### Scenario: A button that is not there is refused

- **WHEN** a test clicks a `callback_data` that the given message does not carry
- **THEN** the trigger fails as a setup error, and nothing is dispatched

### Requirement: A skipped handler is not reported as the one that ran

Routing diagnostics SHALL not report a handler that raised `SkipHandler` or `CancelHandler`
as the handler that ran, nor record that control-flow exception as its error.

#### Scenario: A skipping handler falls through

- **WHEN** the first matching handler raises `SkipHandler` and a later one handles the
  update
- **THEN** the route names the later handler, with no exception

### Requirement: A user's edit has Telegram's shape

An edit trigger SHALL set `edit_date`, SHALL change only the fields the test passes, and
SHALL refuse, as a setup error, to edit a message the actor did not send. An edited message
fed by hand SHALL replace the stored message with the same id.

#### Scenario: An edit is dated

- **WHEN** a user actor edits a message it sent
- **THEN** the dispatched message carries an `edit_date`

#### Scenario: A user cannot edit the bot's message

- **WHEN** a user actor edits a message the bot sent
- **THEN** the trigger fails as a setup error

### Requirement: Drain reports only unretrieved exceptions

`drain()` SHALL report a finished task's exception only if nothing retrieved it.

#### Scenario: A caught failure is not reported

- **WHEN** a handler awaits a task that fails and catches the exception
- **THEN** `drain()` raises nothing for it

### Requirement: Business connection updates name the owner

A business connection update SHALL carry the account owner as its user, whoever triggers
it.

#### Scenario: A customer-bound actor disables the connection

- **WHEN** an actor bound to a business connection it does not own disables it
- **THEN** the update's user is the account owner

### Requirement: Payment and subscription triggers carry documented fields

The subscription trigger SHALL take its state, refusing a value other than `active`,
`canceled` or `failed`. A subscription payment SHALL carry its expiry date and
first-recurring flag.

#### Scenario: A cancelled subscription can be tested

- **WHEN** a test triggers a subscription update with state `canceled`
- **THEN** the handler receives that state

### Requirement: Inline queries carry their chat type

An inline query trigger SHALL set `chat_type`: `sender` for the actor's own private chat
with the bot, and the chat's type otherwise.

#### Scenario: An inline query from a group

- **WHEN** an actor bound to a supergroup triggers an inline query
- **THEN** the query's `chat_type` is `supergroup`

### Requirement: Votes respect the poll's rules

A vote trigger SHALL refuse, as a setup error, an option the poll does not have, several
options on a poll that does not allow multiple answers, and a changed vote on a poll that
does not allow revoting.

#### Scenario: Two answers on a single-answer poll

- **WHEN** a user votes for two options on a single-answer poll
- **THEN** the trigger fails as a setup error, and no answer is dispatched

### Requirement: Guest messages can be answered

A guest message trigger SHALL carry a `guest_query_id`, unique in the world, SHALL accept
field overrides, and its message SHALL be registered like other carried messages. Answering
it stays record-only.

#### Scenario: The canonical guest handler works

- **WHEN** a handler answers a guest message through its `guest_query_id`
- **THEN** the answer is accepted
