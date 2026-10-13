## ADDED Requirements

### Requirement: The world has a clock the test controls

World time SHALL stand still unless the test advances it. Advancing SHALL accept a number
of seconds or a duration and SHALL refuse a negative one. Every date the world produces
(messages, events, transactions) SHALL be the clock's current time. Advancing SHALL
dispatch the updates that the passing time causes before it returns, in the order their
moments occur. The host machine's clock SHALL never be consulted.

#### Scenario: Time does not move on its own

- **WHEN** a test feeds several updates without advancing the clock
- **THEN** every message they produce carries the same date

#### Scenario: Advancing moves every later date

- **WHEN** a test advances the clock by one hour and a user then sends a message
- **THEN** that message's date is one hour after the dates produced before the advance

#### Scenario: Time cannot go backwards

- **WHEN** a test advances the clock by a negative amount
- **THEN** the call fails, and the clock is unchanged

### Requirement: Restrictions and bans expire

An `until_date` given as a duration SHALL be measured from the clock. An `until_date` less
than 30 seconds or more than 366 days ahead SHALL mean forever, and forever SHALL be
reported as `0`. Once the clock passes a stored `until_date`, membership reads SHALL show
the restriction lifted: a restricted member reads as a member, and a banned user reads as
having left.

#### Scenario: A mute lifts on time

- **WHEN** a handler restricts a member for one hour, and the test advances the clock by
  one hour
- **THEN** reading that member reports an ordinary member

#### Scenario: A ban lifts on time

- **WHEN** a handler bans a user for one day, and the test advances the clock by one day
- **THEN** reading that user reports that they have left the chat

#### Scenario: A short or very long period means forever

- **WHEN** a handler restricts a member until 10 seconds from now, or until 400 days from
  now
- **THEN** the member reads as restricted with `until_date` `0`, and advancing the clock by
  any amount does not lift it

#### Scenario: A duration counts from now

- **WHEN** the test has advanced the clock, and a handler then restricts a member with a
  duration of one hour
- **THEN** the stored `until_date` is one hour after the clock's current time

### Requirement: Polls close on schedule

A poll sent with an open period or a close date SHALL close when the clock reaches that
moment. The bot SHALL receive a `poll` update carrying the closed poll, and voting in it
SHALL be refused as it is in a stopped poll. A close date or open period less than 5
seconds or more than 2628000 seconds ahead SHALL fail as a Telegram error.

#### Scenario: A poll closes when its period ends

- **WHEN** a handler sends a poll with a 60-second open period, and the test advances the
  clock by 60 seconds
- **THEN** a `poll` update is dispatched whose poll is closed, and the stored poll is closed

#### Scenario: A poll stays open before its time

- **WHEN** the test advances the clock by less than the open period
- **THEN** no `poll` update is dispatched, and users can still vote

#### Scenario: An out-of-range close date is rejected

- **WHEN** a handler sends a poll whose close date is 2 seconds ahead
- **THEN** the call raises `TelegramBadRequest`, and no poll is stored

### Requirement: Live locations expire

Editing a live location SHALL fail once its live period has elapsed since the message was
sent, unless the period is forever (`0x7FFFFFFF`). A new live period SHALL be refused when
it exceeds the current period by more than a day, or when it would end more than 90 days
after the clock's current time.

#### Scenario: Editing within the period works

- **WHEN** a handler sends a live location for 10 minutes and edits it 5 minutes later
- **THEN** the stored location carries the new coordinates

#### Scenario: Editing after the period fails

- **WHEN** the test advances the clock past the live period and the handler edits the
  location
- **THEN** the call raises `TelegramBadRequest`, and the stored location is unchanged

#### Scenario: A forever location never expires

- **WHEN** a handler sends a live location with the forever period and the test advances
  the clock by a year
- **THEN** editing it still works

#### Scenario: Extending by more than a day is refused

- **WHEN** a handler edits a one-hour live location with a period two days longer
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Old messages cannot be deleted or edited

Deleting a message sent 48 hours or more before the clock's current time SHALL fail as a
Telegram error, and a dice in a private chat SHALL be deletable only once more than 24
hours have passed. Batch deletion SHALL skip such messages. Editing a
business message the bot did not send and that carries no inline keyboard SHALL fail once
more than 48 hours have passed.

#### Scenario: A fresh message can be deleted

- **WHEN** a handler deletes a message sent an hour earlier
- **THEN** the message is removed

#### Scenario: A two-day-old message cannot be deleted

- **WHEN** the test advances the clock by 48 hours and a handler deletes an earlier message
- **THEN** the call raises `TelegramBadRequest`, and the message stays

#### Scenario: A fresh dice in a private chat cannot be deleted

- **WHEN** a handler deletes a dice it just sent in a private chat
- **THEN** the call raises `TelegramBadRequest`, and the same call succeeds once more than
  24 hours have passed

#### Scenario: Batch deletion skips messages too old to delete

- **WHEN** a handler batch-deletes one fresh and one two-day-old message
- **THEN** the fresh one is removed, the old one stays, and the call succeeds

#### Scenario: An old business message cannot be edited

- **WHEN** a handler edits a business message sent by the account owner, carrying no inline
  keyboard, 49 hours after it was sent
- **THEN** the call raises `TelegramBadRequest`

### Requirement: A pre-checkout query must be answered within 10 seconds

Answering a pre-checkout query once more than 10 seconds have passed since it was issued
SHALL fail as an expired query, the same way answering an unknown query does.

#### Scenario: A prompt answer succeeds

- **WHEN** a handler answers a pre-checkout query without the clock moving
- **THEN** the answer is accepted

#### Scenario: A late answer fails

- **WHEN** the test advances the clock by 11 seconds before the bot answers a pending
  pre-checkout query
- **THEN** the answer raises `TelegramBadRequest`, reporting the query as too old

### Requirement: An ephemeral command must be answered within 15 seconds

A reply to an incoming ephemeral message SHALL fail as a Telegram error once more than 15
seconds have passed since that message was sent.

#### Scenario: A prompt reply succeeds

- **WHEN** a handler replies to an ephemeral command without the clock moving
- **THEN** the reply is stored for its receiver

#### Scenario: A late reply fails

- **WHEN** the test advances the clock by 16 seconds and the bot then replies to the
  command
- **THEN** the call raises `TelegramBadRequest`, and nothing is stored
