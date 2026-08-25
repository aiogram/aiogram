## MODIFIED Requirements

### Requirement: Only start links are followed, and the rest are refused by name

The toolkit SHALL recognize the deep-link forms `https://t.me/<username>` — including its
`http://` and schemeless spellings — and `tg://resolve?domain=<username>`, and SHALL treat a
link with no query as a plain start. A `start` payload SHALL be honored alongside any other
query parameter, since a real client reads the parameter it recognizes and ignores the rest.
That precedence SHALL hold over the other recognized kinds too, in either query order: a link
carrying both `start` and a Mini App, group or channel launch SHALL be followed as the start
it also is, because that is the shape Telegram hands out so that a client which cannot open
the app still opens the bot.

Every other recognized kind SHALL be refused with a message naming the kind and what a real
client would do with it, rather than being replayed as a plain start: group, Mini App, channel
and attachment-menu launches, chat invite links, links carrying extra path segments such as
message links and Mini App shortlinks, and any query the toolkit does not recognize. A url
that is not a Telegram link at all SHALL be refused as such. The precedence above SHALL need
a real `start` to take it, so one of those kinds appearing alone is refused as before.

#### Scenario: A bare profile link replays as a plain start

- **WHEN** the button's url is `https://t.me/<bot>` with no query
- **THEN** following it sends `/start` with no payload

#### Scenario: An explicit start wins over a start-ish parameter beside it

- **WHEN** the button's url carries both `start` and one of `startapp`, `startgroup` or
  `startchannel`, in either order
- **THEN** following it sends `/start` with the `start` payload rather than being refused

#### Scenario: An unsupported kind is named, not downgraded

- **WHEN** the button opens a group chooser, a Mini App, a channel chooser or the attachment
  menu, with no `start` beside it
- **THEN** following it raises, naming that kind and what to do instead, rather than sending
  a plain `/start`

#### Scenario: An unrecognized query is refused rather than guessed

- **WHEN** the button's url carries a query parameter the toolkit does not define
- **THEN** following it raises, saying that what a real client would do with it is not
  simulated

#### Scenario: The scan skips what it cannot follow

- **WHEN** a keyboard carries both an unfollowable deep link and a real start link to this bot
- **THEN** the start link is followed; and when only unfollowable ones are present, the
  failure names each url and why it was rejected

### Requirement: A user's own private chat opens on demand

A blueprint SHALL NOT have to declare a user's private chat with the bot: every Telegram user
can open one, so the environment SHALL create it, shaped exactly as a declared one, the first
time it is needed on a *user-driven* path — when a deep link is followed, when an unbound
actor sends, and when an actor binds to its own id. Any *other* chat the blueprint never
declared SHALL still be refused, since the world cannot invent a group's title, type or
membership from an identifier.

The bot's own calls SHALL open nothing. A real bot cannot write into a private chat first — it
may only answer a user who wrote to it — so a chat named by an outbound call and not declared
SHALL be reported as a gap in the test's setup rather than opened on demand.

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

#### Scenario: The bot writing first does not open one

- **WHEN** a handler sends a message to a declared user whose private chat was never declared
  and never opened
- **THEN** the call raises rather than opening the chat, because a real bot cannot start the
  conversation

### Requirement: Everything the world hands out carries the bot

Every object the environment gives to the code under test SHALL be bound to a `Bot` the way
a parsed Bot API response is, so that its shortcuts work — including objects nested inside a
result and the items of a list result. This SHALL hold for modeled, synthesized and
overridden results alike, and SHALL also hold for objects read directly out of the world,
whoever put them there: a message a user actor sent, and a service message produced as a
side effect of a modeled call.

An object that already carries a bot belongs to whoever owns it and SHALL NOT be re-bound,
so a second `Bot` sharing the environment's session never takes over the world's own
objects.

The binding SHALL be a property of the world's chat registry rather than of one moment in its
life: a chat SHALL be wired to its world however it is registered, including when the whole
mapping is replaced after construction, so that messages stored afterwards are bound as usual.

#### Scenario: A shortcut on a result reaches the world

- **WHEN** a handler sends a message and calls `edit_text` on the returned `Message`
- **THEN** the edit is applied to the stored message, without the test attaching a bot by hand

#### Scenario: Nested objects and list items are bound too

- **WHEN** a result carries another object inside it, or the result is a list
- **THEN** shortcuts work on the nested object and on every item of the list

#### Scenario: A message no call returned is usable

- **WHEN** a user actor sends a message and the test reads it back out of the chat
- **THEN** calling a shortcut on it works, exactly as on a message a call returned

#### Scenario: An object the world already owns is not re-bound

- **WHEN** a second `Bot` shares the environment's session and a call through it returns a
  message the world already stored
- **THEN** that message stays bound to the environment's own bot, while objects minted for
  that call are bound to the calling bot

#### Scenario: Replacing the chat mapping does not detach the world

- **WHEN** a test assigns a plain mapping of chats to the world after it was built
- **THEN** those chats are wired to the world as declared ones are, and messages stored in
  them afterwards carry the bot

### Requirement: Objects a test hands to a call stay the test's own

Values the code under test passes into a Bot API call SHALL be copied before they reach
world state, so an object a test declares once — a shared `reply_markup`, a
`ChatPermissions` constant, a list of commands — is never mutated, never bound to a bot, and
never keeps a disposed environment alive. The value objects the world stores SHALL likewise
be copied on the way out. A `Message` is the deliberate exception: the message a call returns
is the one the chat holds.

A value that already belongs to *this* environment's bot is the world's own object, not the
caller's, and SHALL be passed through by identity instead of copied — so a stored message
named as a field keeps tracking later edits to it, and two fields naming one stored object go
on sharing it. That rule SHALL be the same one on every path a value enters the world by: a
trigger's fields and an edit's changes SHALL NOT disagree about the same value. Ownership
SHALL be decided by identity, so a value belonging to a *different* environment is still
copied.

#### Scenario: A shared constant is not captured by the world

- **WHEN** a test passes the same module-level `reply_markup` to a call in several tests
- **THEN** the constant is unbound and unchanged afterwards, and the world holds a copy

#### Scenario: The call log shows what the caller built

- **WHEN** a test asserts on a recorded call after the world has stored the same values
- **THEN** the recorded entry carries the values the code under test passed, not the copies
  the world went on to keep

#### Scenario: Reading state back does not bind it

- **WHEN** a handler sets chat permissions and a later `getChat` returns them
- **THEN** the returned permissions are a copy, and the permissions the world stores still
  compare equal to the constant the test declared

#### Scenario: A returned message is the stored message

- **WHEN** a handler sends a message
- **THEN** the returned `Message` is the same object the chat's message list holds

#### Scenario: A declared override result is answered fresh each time

- **WHEN** a test declares a result once and the method is called several times
- **THEN** each call is answered with its own copy, and the declared object is neither
  mutated nor left bound to any bot

#### Scenario: An edit aliases what a send aliases

- **WHEN** a test names a message the world already holds in the fields of an edit trigger,
  as it would in the fields of a send
- **THEN** the stored message points at that very object, and two fields naming it share it

#### Scenario: A value from another environment is still copied

- **WHEN** a trigger field names an object bound to a different environment's bot
- **THEN** the world stores a copy bound to this environment's bot, and the original is left
  as it was

### Requirement: A gap in the test's own setup fails the test, not the bot

A refusal caused by something the blueprint never declared, or by a surface the toolkit does
not model, SHALL be raised as `WorldLookupError`, which the environment never converts into a
Telegram error. It SHALL propagate out of the call the bot made and fail the test, so the
bot's own error handling cannot swallow it and leave a green test that exercised the wrong
branch. Its message SHALL say what to declare or how to proceed.

The two kinds SHALL be distinguishable by type: `ApiRejection` is something Telegram itself
would answer, and is what `handle_call` turns into a `TelegramBadRequest`, while
`WorldLookupError` is not.

A chat named by an outbound call and not declared SHALL be one of these gaps. Because the
wording Telegram uses for it — "chat not found" — is a branch bots really do handle, reporting
it as a Telegram error let a missing declaration run the blocked-user path and pass. Its
message SHALL enumerate the chats the world does declare, SHALL point at the declaration and
the on-demand helper that would add the missing one, and SHALL name the override that produces
the real API refusal for a test that wants that branch.

#### Scenario: An undeclared entity is not reported as a Bad Request

- **WHEN** a handler calls a method naming a user, chat, sticker set, poll, gift, charge or
  business connection the blueprint never declared
- **THEN** the call raises `WorldLookupError` rather than `TelegramBadRequest`, and the
  message names what is missing

#### Scenario: An undeclared chat says what this world has

- **WHEN** an outbound call names a chat identifier or `@username` the blueprint never
  declared
- **THEN** the failure lists the declared chats with their type and readable name, or says the
  world declares none, and names how to declare the missing one

#### Scenario: A declared user with no private chat is told exactly that

- **WHEN** the identifier belongs to a declared user whose private chat was never opened
- **THEN** the failure says a bot cannot write first, and names declaring the chat, opening it
  through the world, and having the user write first

#### Scenario: The real refusal stays testable

- **WHEN** a test declares `TelegramBadRequest` with Telegram's "chat not found" wording as
  the outcome of the sending method
- **THEN** the bot's own `except TelegramBadRequest` branch runs, without the world pretending
  to be short of a chat

#### Scenario: The bot's own error handling cannot hide it

- **WHEN** the bot under test wraps its calls in `except TelegramBadRequest`
- **THEN** a setup gap still reaches the test, because it is not a Telegram error

#### Scenario: Something the toolkit does not model says so

- **WHEN** a handler edits a message addressed by `inline_message_id`
- **THEN** the call raises `WorldLookupError` naming inline messages as unmodeled, rather
  than claiming Telegram refused it

#### Scenario: Reaching into the world directly surfaces the rejection unconverted

- **WHEN** a test asks a chat for a message or a topic that is not there, outside any call
- **THEN** `ApiRejection` is raised as it is, since there is no call to convert it into a
  Telegram error

### Requirement: Waiting for a condition the bot reaches on its own

The environment SHALL provide a way to wait for an arbitrary condition, re-checking it and
yielding to the event loop in between so that background work the trigger did not await can
run. The condition SHALL be allowed to be synchronous or to return an awaitable, and whatever
truthy value it produces SHALL be returned, so a wait can fetch as well as test. The wait
SHALL be satisfied immediately when the condition already holds, and SHALL NOT exceed its
stated timeout whatever polling interval it was given.

The description of what is awaited SHALL be the second **positional** parameter, since these
waits are written with lambdas and that description is the only thing a failure message can
say about one; it SHALL still be accepted as a keyword. The timing parameters SHALL stay
keyword-only.

#### Scenario: A background task satisfies the wait

- **WHEN** a handler schedules work that changes the world after it returns, and the test
  waits for that change
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

#### Scenario: The description is passed without ceremony

- **WHEN** a test passes what it is waiting for as the argument after the predicate
- **THEN** a timeout quotes it, exactly as when it is passed by keyword

### Requirement: Waiting for a message in a chat or a topic

A chat SHALL provide a wait for a message matching a predicate, and a forum topic SHALL
provide the same wait over its own messages, so a message posted into a sibling topic never
satisfies it. The predicate SHALL be matched against every message the view holds, not only
the ones arriving after the call; an omitted predicate SHALL match any message. The message
returned SHALL be usable like any other object the world holds.

When more than one message matches, the one with the **highest `message_id`** SHALL be
returned — the newest as Telegram numbers them, rather than whichever the view holds last, so
the result does not depend on the list happening to be sorted.

Both forms SHALL take the description of what is awaited as their second positional
parameter, on the same terms as the condition wait.

#### Scenario: A message that is already there matches

- **WHEN** the message being waited for arrived before the wait started
- **THEN** the wait returns it immediately

#### Scenario: The newest match wins, by identifier

- **WHEN** several messages in the chat match the predicate, in whatever order the view holds
  them
- **THEN** the one with the highest `message_id` is returned

#### Scenario: A topic waits only on its own thread

- **WHEN** a matching message is posted into a different topic of the same chat
- **THEN** the wait is not satisfied by it

#### Scenario: What the wait returns is usable

- **WHEN** a test calls a shortcut on the message a wait returned
- **THEN** it works, exactly as on any message read out of the world

#### Scenario: A message wait names what it wanted

- **WHEN** a chat or topic wait is given a description as its second argument and times out
- **THEN** the failure quotes it rather than only the predicate's identity

### Requirement: Promotion and restriction persist what they granted

`promoteChatMember` SHALL store the whole rights mask the request carried, so a right the
request did not pass is not granted and is reported as such. A request in which no right comes
out true SHALL demote the member, as the Bot API documents; any right that is true — including
the anonymity flag alone — SHALL keep the member an administrator. A demotion SHALL also clear
the member's custom title, since that is an administrator's and the plain-member variant has no
field for one; the member's tag SHALL survive it. `restrictChatMember` SHALL clear any
administrator rights the member held.

`restrictChatMember` and `setChatPermissions` SHALL store what the request *grants* rather than
the mask it passed. Unless the request sets `use_independent_chat_permissions`, granting
permission to send other message kinds or web page previews SHALL grant every kind of message,
and granting polls SHALL grant messages — so the permissions read back may be broader than the
ones handed in, as they are against the real API. Independently of that switch, a permission
the request leaves unset SHALL take the value of the one the Bot API documents it as following.
Neither method SHALL mutate or retain the caller's own permissions object.

#### Scenario: A promotion grants exactly what was asked for

- **WHEN** a handler promotes a member passing only one right
- **THEN** reading the member back reports that right as granted and the others as not

#### Scenario: A second promotion replaces the first

- **WHEN** a handler promotes the same member again with a different set of rights
- **THEN** the member holds the second set, not the union of both

#### Scenario: Hiding an administrator is not a demotion

- **WHEN** a handler promotes a member passing only the anonymity flag
- **THEN** the member remains an administrator

#### Scenario: A promotion that grants nothing demotes

- **WHEN** a handler promotes a member passing no rights, or every right as false
- **THEN** the member becomes an ordinary member, and can be promoted again later

#### Scenario: A demotion does not leave a title behind

- **WHEN** a member with a custom title is demoted and later promoted again
- **THEN** the later promotion reports no custom title, since none was granted

#### Scenario: A demotion keeps the member's tag

- **WHEN** a member carrying a tag is demoted
- **THEN** `getChatMember` reports the tag on the plain-member result

#### Scenario: A restriction stores what it grants

- **WHEN** a handler restricts a member granting only other message kinds
- **THEN** `getChatMember` reports every message kind as permitted, because the Bot API
  couples them

#### Scenario: Independent permissions are stored as passed

- **WHEN** the same restriction sets `use_independent_chat_permissions`
- **THEN** only the permission that was passed is reported as granted

#### Scenario: An omitted permission follows the one it defaults to

- **WHEN** a request grants a permission that another one defaults to, with or without
  independent permissions
- **THEN** the dependent permission is reported as granted too

#### Scenario: Setting chat permissions applies the same couplings

- **WHEN** a handler sets chat permissions granting other message kinds
- **THEN** a later `getChat` reports every message kind as permitted

### Requirement: Member annotations are stored and read back

Setting an administrator's custom title or a member's tag SHALL write to that member's
stored state, and `getChatMember` SHALL surface both. The two apply to different members
and SHALL enforce that distinction: a custom title belongs to an administrator, while a
tag belongs to a regular member. That distinction SHALL hold over time as well as at the
moment of writing: losing the administrator status SHALL take the custom title with it, while
a tag SHALL outlive any status change, because the Bot API carries it on every membership
variant.

#### Scenario: Custom title round-trips

- **WHEN** a handler promotes a user and sets a custom title for them
- **THEN** `getChatMember` for that user reports the custom title

#### Scenario: A custom title for a non-administrator fails

- **WHEN** a handler sets a custom title for an ordinary member
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Member tag round-trips

- **WHEN** a handler sets a tag for a regular member
- **THEN** `getChatMember` for that user reports the tag

#### Scenario: A tag on an administrator fails

- **WHEN** a handler sets a tag for an administrator
- **THEN** the call raises `TelegramBadRequest`, because the Bot API tags regular members

## ADDED Requirements

### Requirement: A chat's messages are ordered by identifier

The list of messages a chat holds SHALL be kept in ascending `message_id` order as messages
are stored, so that reading its last element means the newest message whoever produced it.
Almost every producer allocates its identifier from the chat itself, but a message an update
carried in from another environment was numbered there, and appending one could leave the list
unsorted. The identifier a message carries SHALL NOT be rewritten to achieve the ordering,
since it is how a test correlates what it fed with what the world holds.

#### Scenario: A message carried in from elsewhere lands in order

- **WHEN** an update built by another environment carries a message older than the ones the
  destination chat already holds, and is fed to this one
- **THEN** the chat's messages are still in ascending identifier order, and its last element is
  the newest message rather than the carried one

#### Scenario: The carried identifier is preserved

- **WHEN** such a message is registered
- **THEN** it is found under the identifier it arrived with

### Requirement: One wait timeout for a whole environment

An environment SHALL accept a default timeout for every wait it owns, so a bot whose
background work is slow, or a suite that would rather fail fast than pause on every timing
bug, states it once instead of on every call. It SHALL apply to the condition wait and to
every chat and topic message wait alike, SHALL be reachable by a chat added after the
environment was built, and SHALL be overridden by an explicit timeout on a single call. Absent
any setting, the default SHALL be five seconds.

#### Scenario: One setting reaches every wait

- **WHEN** an environment is built with a default wait timeout and a condition wait, a chat
  wait and a topic wait each time out
- **THEN** all three gave up after that timeout

#### Scenario: A single call can still say otherwise

- **WHEN** one wait passes its own timeout
- **THEN** that call uses it while the rest of the environment keeps the default

#### Scenario: The setting is configuration, not state

- **WHEN** two worlds hold the same chats, users and messages but were given different wait
  timeouts
- **THEN** they still compare equal
