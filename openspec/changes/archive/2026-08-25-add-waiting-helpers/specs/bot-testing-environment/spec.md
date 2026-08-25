## ADDED Requirements

### Requirement: Waiting for a condition the bot reaches on its own

The environment SHALL provide a way to wait for an arbitrary condition, re-checking it and
yielding to the event loop in between so that background work the trigger did not await can
run. The condition SHALL be allowed to be synchronous or to return an awaitable, and whatever
truthy value it produces SHALL be returned, so a wait can fetch as well as test. The wait SHALL
be satisfied immediately when the condition already holds, and SHALL NOT exceed its stated
timeout whatever polling interval it was given.

#### Scenario: A background task satisfies the wait

- **WHEN** a handler schedules work that changes the world after it returns, and the test waits
  for that change
- **THEN** the wait returns once the work has run

#### Scenario: An already-true condition costs nothing

- **WHEN** the condition holds before the wait starts
- **THEN** it returns without yielding to the event loop first

#### Scenario: The wait returns what it found

- **WHEN** the condition produces a value rather than a plain flag
- **THEN** that value is returned to the test

#### Scenario: The timeout is honored

- **WHEN** a wait is given a polling interval coarser than the time left
- **THEN** it gives up at the timeout rather than overshooting by a whole interval

### Requirement: Waiting for a message in a chat or a topic

A chat SHALL provide a wait for a message matching a predicate, and a forum topic SHALL provide
the same wait over its own messages, so a message posted into a sibling topic never satisfies
it. The predicate SHALL be matched against every message the view holds, not only the ones
arriving after the call, and the newest match SHALL be returned; an omitted predicate SHALL
match any message. The message returned SHALL be usable like any other object the world holds.

#### Scenario: A message that is already there matches

- **WHEN** the message being waited for arrived before the wait started
- **THEN** the wait returns it immediately

#### Scenario: The newest match wins

- **WHEN** several messages in the chat match the predicate
- **THEN** the most recent one is returned

#### Scenario: A topic waits only on its own thread

- **WHEN** a matching message is posted into a different topic of the same chat
- **THEN** the wait is not satisfied by it

#### Scenario: What the wait returns is usable

- **WHEN** a test calls a shortcut on the message a wait returned
- **THEN** it works, exactly as on any message read out of the world

### Requirement: A predicate that raises does not fail the wait

Because a chat holds messages of every shape, an exception raised by a message predicate SHALL
count as "does not match" rather than ending the wait. Such exceptions SHALL NOT be swallowed:
if the wait times out, the failure SHALL report what the predicate raised and on which message.

#### Scenario: A service message does not break a text predicate

- **WHEN** the chat contains a service message with no text and the predicate reads the text
- **THEN** the wait continues and is satisfied by the message it was actually asking about

#### Scenario: A predicate that always raises still fails with its cause

- **WHEN** the predicate raises on every message and the wait times out
- **THEN** the failure names the exception type, its message and the message it happened on

### Requirement: A wait that gives up says what it was waiting for

Every waiting helper SHALL fail with a `WaitTimeoutError`, which SHALL be a `TimeoutError`, and
its message SHALL name what was awaited and show the state that was there instead — the
messages the chat or topic holds, or the description the test gave for a condition.

#### Scenario: A generic timeout assertion catches it

- **WHEN** a test asserts that a wait raises the built-in `TimeoutError`
- **THEN** the assertion holds

#### Scenario: The failure enumerates what was there

- **WHEN** a wait for a message times out
- **THEN** the message lists the messages the chat or topic holds, identifying each one

#### Scenario: A condition names itself when the test said so

- **WHEN** a wait for a condition is given a description and times out
- **THEN** the failure quotes that description rather than only the predicate's identity
