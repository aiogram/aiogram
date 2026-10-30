## ADDED Requirements

### Requirement: The world has a clock the test controls

World time SHALL start at the real time, to the second, or at a start the test gives, and
SHALL then stand still unless the test advances it, never backwards. A date for something
happening now SHALL be the clock's time. Advancing SHALL dispatch the updates time causes
before returning, ordered by moment and then by scheduling order.

#### Scenario: The clock starts at the real time

- **WHEN** a test builds an environment without giving a start
- **THEN** the clock reads the real time to the second, so a date a bot computes from the
  real clock lands where Telegram would see it

#### Scenario: A pinned start makes dates reproducible

- **WHEN** a test builds an environment with a fixed start
- **THEN** the clock reads that start until the test advances it

#### Scenario: Time does not move on its own

- **WHEN** a test feeds several updates without advancing the clock
- **THEN** every message they produce carries the same date

#### Scenario: Advancing moves every later date

- **WHEN** a test advances the clock by one hour and a user then sends a message
- **THEN** that message's date is one hour after the dates produced before the advance

#### Scenario: Time cannot go backwards

- **WHEN** a test advances the clock by a negative amount
- **THEN** the call fails, and the clock is unchanged

#### Scenario: Advancing cannot overlap itself

- **WHEN** a handler running inside an advance, or a concurrent task, advances the clock
- **THEN** that call fails as a setup error, and the running advance is unaffected

#### Scenario: Events due during an advance fire within it

- **WHEN** a handler reacting to an event during an advance schedules another event that
  falls before the advance's target
- **THEN** that event also fires before the advance returns, at its own moment

### Requirement: Restrictions and bans expire

An `until_date` given as a duration SHALL be measured from the clock. One less than 30
seconds or more than 366 days ahead SHALL mean forever. Once the clock reaches a stored
`until_date`, every membership read SHALL see the restriction ended: a present restricted
user reads as a member, an absent one and a banned user as having left, carrying no end
date.

#### Scenario: A mute lifts on time

- **WHEN** a handler restricts a member for one hour, and the test advances the clock by
  one hour
- **THEN** reading that member reports an ordinary member with no `until_date`

#### Scenario: A mute on an absent user ends as left

- **WHEN** a handler restricts a user who is not in the chat for one hour, and the test
  advances the clock by one hour
- **THEN** reading that user reports that they have left

#### Scenario: A ban lifts on time

- **WHEN** a handler bans a user for one day, and the test advances the clock by one day
- **THEN** reading that user reports that they have left the chat

#### Scenario: A short or very long period means forever

- **WHEN** a handler restricts a member until 10 seconds from now, or until 400 days from
  now
- **THEN** the member reads as restricted with `until_date` at the Unix epoch, and advancing
  the clock by any amount does not lift it

#### Scenario: A duration counts from now

- **WHEN** the test has advanced the clock, and a handler then restricts a member with a
  duration of one hour
- **THEN** the stored `until_date` is one hour after the clock's current time

### Requirement: Polls close on schedule

A poll sent with an open period or a close date, never both, SHALL close when the clock
reaches that moment: the stored poll and its message SHALL show it closed, the bot SHALL
receive a `poll` update with it, and voting SHALL be refused. A moment less than 5 or more
than 2628000 seconds ahead SHALL fail as a Telegram error. A poll stopped earlier SHALL not
close again.

#### Scenario: A poll closes when its period ends

- **WHEN** a handler sends a poll with a 60-second open period, and the test advances the
  clock by 60 seconds
- **THEN** a `poll` update is dispatched whose poll is closed, and the stored poll and the
  message carrying it are closed

#### Scenario: A poll stays open before its time

- **WHEN** the test advances the clock by less than the open period
- **THEN** no `poll` update is dispatched, and users can still vote

#### Scenario: A stopped poll does not close twice

- **WHEN** a handler stops a scheduled poll and the test then advances past its close
  moment
- **THEN** no `poll` update is dispatched for it

#### Scenario: An invalid schedule is rejected

- **WHEN** a handler sends a poll whose close date is 2 seconds ahead, or that passes both
  an open period and a close date
- **THEN** the call raises `TelegramBadRequest`, and no poll is stored

### Requirement: Live locations expire

Editing or stopping a live location SHALL fail once its live period has elapsed since the
message was sent, after `stopMessageLiveLocation`, or when the location was never live,
unless the period is forever (`0x7FFFFFFF`). A new live period other than forever SHALL be refused
when it exceeds the current one by more than a day, or ends more than 90 days after the
clock's time.

#### Scenario: Editing within the period works

- **WHEN** a handler sends a live location for 10 minutes and edits it 5 minutes later
- **THEN** the stored location carries the new coordinates

#### Scenario: Editing after the period fails

- **WHEN** the test advances the clock past the live period and the handler edits the
  location
- **THEN** the call raises `TelegramBadRequest`, and the stored location is unchanged

#### Scenario: Editing a stopped location fails

- **WHEN** a handler stops a live location and then edits it
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Stopping an expired location fails

- **WHEN** the test advances the clock past a live location's period and the handler stops
  it
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: A forever location never expires

- **WHEN** a handler sends a live location with the forever period and the test advances
  the clock by a year
- **THEN** editing it still works

#### Scenario: Extending by more than a day is refused, forever is not

- **WHEN** a handler edits a one-hour live location with a period two days longer, and then
  with the forever period
- **THEN** the first call raises `TelegramBadRequest` and the second succeeds

### Requirement: Old messages cannot be deleted or edited

Deleting a message sent 48 hours or more before the clock's time SHALL fail as a Telegram
error, and a dice in a private chat SHALL be deletable only once more than 24 hours have
passed. Batch deletion SHALL skip such messages, which is the toolkit's reading. Editing
the text, caption, media or markup of a business message not sent by the bot and carrying
no inline keyboard SHALL fail once more than 48 hours have passed.

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
- **THEN** the call raises `TelegramBadRequest`, while a business message the bot sent stays
  editable

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

## MODIFIED Requirements

### Requirement: Outstanding queries are tracked and answers validated

Every trigger that produces a query — callback query, inline query, shipping query,
pre-checkout query — SHALL register that query's identifier as outstanding. The
corresponding answer methods SHALL be applied to that registry: answering an outstanding
query SHALL succeed and clear it, and answering an unknown or already-answered identifier
SHALL raise `TelegramBadRequest`, as Telegram does when a query has expired or was already
answered. A pre-checkout query SHALL count as expired once more than 10 seconds have passed
on the world clock since it was issued, as the Bot API documents; the other kinds have no
documented limit and do not expire.

#### Scenario: Answering an outstanding callback query succeeds

- **WHEN** a handler answers the callback query it is currently processing
- **THEN** the call succeeds and the query is no longer outstanding

#### Scenario: Answering twice fails

- **WHEN** a handler answers the same callback query a second time
- **THEN** the second call raises `TelegramBadRequest`

#### Scenario: Answering a fabricated identifier fails

- **WHEN** a handler answers a callback query identifier the environment never issued
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: The rule covers every query kind

- **WHEN** an inline query, a shipping query or a pre-checkout query is answered with an
  identifier that is not outstanding
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: A late pre-checkout answer fails

- **WHEN** the test advances the clock by 11 seconds before the bot answers a pending
  pre-checkout query
- **THEN** the answer raises `TelegramBadRequest`, reporting the query as too old

#### Scenario: Other queries do not expire

- **WHEN** the test advances the clock by an hour before the bot answers a pending callback
  query
- **THEN** the answer succeeds

### Requirement: Polls are world state

A poll sent by the bot SHALL be stored on the message that carries it, holding its
question, options, type, anonymity, multiple-answer flag, quiz answer and explanation,
the votes cast, whether it is closed, and when it is scheduled to close. A blueprint SHALL
be able to declare an existing poll.

#### Scenario: A sent poll is stored on its message

- **WHEN** a handler calls `sendPoll`
- **THEN** a message carrying that poll is appended to the chat, and the returned message
  is the stored one

#### Scenario: A declared poll is answerable

- **WHEN** a blueprint declares a poll in a chat and a user actor votes in it
- **THEN** the vote is recorded without the poll having been sent through the API first

#### Scenario: A scheduled close is reported

- **WHEN** a handler sends a poll with an open period
- **THEN** the stored poll reports the moment it will close
