## ADDED Requirements

### Requirement: Deep-link buttons can be followed

A user actor SHALL be able to follow a `url` button that deep-links to the bot under test,
with the same validation a callback button gets: the button SHALL have to be carried by a
message the environment actually holds, either a named one or any message of the actor's chat.
Following SHALL replay what tapping causes in a real client — the user's private chat with the
bot receives `/start <payload>`, or a bare `/start` when the link carries none — so filters,
the command parser, middlewares and FSM all run as they do in production.

#### Scenario: Following a group button opens the conversation in the DM

- **WHEN** the bot posts a group message carrying a `t.me` start-link button and a user actor
  follows it
- **THEN** the user's private chat with the bot holds a `/start` message carrying the link's
  payload, and the handler registered for it ran

#### Scenario: The button has to be real

- **WHEN** a test follows a url that no message in scope carries
- **THEN** the call raises, naming the chat or the message it looked in

#### Scenario: A link to another bot is not followable

- **WHEN** the button deep-links to a different bot's username
- **THEN** the call raises rather than sending a `/start` to the bot under test

#### Scenario: The newest followable button is chosen

- **WHEN** no target is given and several messages carry deep-link buttons
- **THEN** the most recent followable link to this bot is the one followed

### Requirement: Only start links are followed, and the rest are refused by name

The toolkit SHALL recognize the deep-link forms `https://t.me/<username>` — including its
`http://` and schemeless spellings — and `tg://resolve?domain=<username>`, and SHALL treat a
link with no query as a plain start. A `start` payload SHALL be honored alongside any other
query parameter, since a real client reads the parameter it recognizes and ignores the rest.

Every other recognized kind SHALL be refused with a message naming the kind and what a real
client would do with it, rather than being replayed as a plain start: group, Mini App, channel
and attachment-menu launches, chat invite links, links carrying extra path segments such as
message links and Mini App shortlinks, and any query the toolkit does not recognize. A url that
is not a Telegram link at all SHALL be refused as such.

#### Scenario: A bare profile link replays as a plain start

- **WHEN** the button's url is `https://t.me/<bot>` with no query
- **THEN** following it sends `/start` with no payload

#### Scenario: An unsupported kind is named, not downgraded

- **WHEN** the button opens a group chooser, a Mini App, a channel chooser or the attachment
  menu
- **THEN** following it raises, naming that kind and what to do instead, rather than sending a
  plain `/start`

#### Scenario: An unrecognized query is refused rather than guessed

- **WHEN** the button's url carries a query parameter the toolkit does not define
- **THEN** following it raises, saying that what a real client would do with it is not simulated

#### Scenario: The scan skips what it cannot follow

- **WHEN** a keyboard carries both an unfollowable deep link and a real start link to this bot
- **THEN** the start link is followed; and when only unfollowable ones are present, the failure
  names each url and why it was rejected

### Requirement: A user's own private chat opens on demand

A blueprint SHALL NOT have to declare a user's private chat with the bot: every Telegram user
can open one, so the environment SHALL create it, shaped exactly as a declared one, the first
time it is needed — when a deep link is followed, when an unbound actor sends, and when an actor
binds to its own id. Any *other* chat the blueprint never declared SHALL still be refused, since
the world cannot invent a group's title, type or membership from an identifier.

#### Scenario: A followed link opens the chat

- **WHEN** a user with no declared private chat follows a start link
- **THEN** the chat exists afterwards, holds the `/start` message, and behaves like a declared
  private chat

#### Scenario: Sending from an unbound actor opens it too

- **WHEN** an actor that was never bound to a chat sends a message
- **THEN** it lands in that user's private chat with the bot

#### Scenario: An undeclared group is still refused

- **WHEN** an actor binds to the identifier of a group nobody declared
- **THEN** the call raises, because the world has nothing to build that chat from
