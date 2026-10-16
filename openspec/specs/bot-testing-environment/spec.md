# bot-testing-environment Specification

## Purpose

The stateful fake Telegram that `aiogram.test` runs bots against: a declarative blueprint
describing a world of chats, users, members, topics, business connections and communities;
isolated environments materialized from it; actors that trigger real updates through the
real dispatcher; and Bot API interception that applies modeled calls to world state,
answers everything else with a schema-valid synthesized result, and records every call for
assertion. Everything crossing the boundary between the world and the code under test is
bound to the environment's bot the way a parsed response is, and copied where the two sides
must not share state.

## Requirements

### Requirement: Environment blueprint declares a reusable world

A blueprint SHALL declare the participants of a test world — chats, users, chat
memberships, the bot's own identity, and default bot properties — without creating any
mutable runtime state. A blueprint SHALL be reusable to materialize any number of
independent environments, and SHALL be usable as a module- or session-scoped value.

#### Scenario: Blueprint describes chats, users and members

- **WHEN** a test declares a blueprint with a private chat, a group chat, two users, and
  one of the users as an administrator of the group
- **THEN** every environment built from that blueprint starts with those chats, users
  and the declared membership status

#### Scenario: Blueprint is not mutated by the environments built from it

- **WHEN** two environments are built from the same blueprint and the first one sends
  messages, bans a member and pins a message
- **THEN** the second environment still reflects the blueprint's original state

#### Scenario: Blueprint supplies bot identity and defaults

- **WHEN** a blueprint declares the bot's `User` fields and `DefaultBotProperties`
- **THEN** `bot.me()` inside the environment returns the declared identity and outgoing
  API calls resolve `Default(...)` sentinels from the declared defaults

### Requirement: Environment materializes an isolated world

An environment SHALL own a `Bot` instance whose session never performs network I/O, a
`Dispatcher` supplied by the test, an FSM storage, and the mutable world state. All state
mutations SHALL be confined to that environment instance.

#### Scenario: No network traffic and no real credentials

- **WHEN** a test runs any bot flow inside an environment
- **THEN** no HTTP request is issued and no valid Telegram token is required

#### Scenario: Environment exposes the framework objects under test

- **WHEN** a test needs the `Bot`, the `Dispatcher`, or the FSM storage
- **THEN** the environment exposes each of them, and they are the same objects the
  handlers receive through dependency injection

### Requirement: Actors trigger updates through the real dispatcher

A user actor bound to a chat SHALL build a schema-valid `Update` and feed it through
`Dispatcher.feed_update`, so that filters, middlewares, dependency injection, FSM state
and routers all execute. The trigger call SHALL return the handler's return value.

#### Scenario: Sending a text message reaches the matching handler

- **WHEN** a user actor sends `"/start"` in a chat
- **THEN** the registered `/start` handler runs through the full routing pipeline and its
  return value is returned to the test

#### Scenario: Filters and middlewares are not bypassed

- **WHEN** a router declares a filter that rejects the triggered event, or a middleware
  that short-circuits it
- **THEN** the handler does not run, exactly as it would in production

#### Scenario: Extra dependencies are injected

- **WHEN** a test passes additional keyword arguments to a trigger call
- **THEN** those values are available to filters, middlewares and handlers through
  aiogram's dependency injection

#### Scenario: Identity of the event is derived from the actor

- **WHEN** a user actor bound to a group chat triggers any event
- **THEN** the resulting update carries that user as the sender and that chat as the
  chat, and `event_from_user` / `event_chat` resolve to them in handlers

### Requirement: Routing diagnostics show where an update went

The environment SHALL report where a fed update actually went, distinct from whatever value
the trigger call returned: whether the dispatcher considered it handled, which handler and
which router claimed it, and the first exception raised inside the middleware chain or the
handler — captured where it was raised even when something further out, such as the
framework's own error-handling middleware, goes on to swallow it. "Handled" SHALL follow the
dispatcher's own definition — something other than "unhandled" came back — which a
middleware that returns without calling the next one already satisfies; the winning
handler's identity SHALL be reported separately, since it is the only field that says
whether a handler actually ran.

This diagnosis SHALL be scoped to a **trigger** rather than to a single update, because one
thing the test did is routinely more than one update: an actor trigger that produces two
updates from one call SHALL group both into the same scope, and the environment SHALL also
let a test open this scope explicitly around several trigger calls of its own. A fed update
outside any explicitly opened scope, and not itself fed from within a handler already
routing one, SHALL open a scope of its own, so the common one-update case needs no explicit
scope at all. The environment SHALL expose every record of the current scope, in the order
each finished routing, and SHALL expose the single most relevant one, preferring in order:
the newest record **carrying an exception**, else the newest **handled** record, else the
newest record of any kind. Both SHALL be empty/absent until the first update is fed.

A scope SHALL belong to the task and the environment that opened it, not to the environment
alone: two scopes opened concurrently SHALL neither share nor discard each other's records, a
fed update SHALL NOT join a scope opened by a different task, and a fed update SHALL NOT join
a scope opened by a *different environment*. Outside any scope open in the current task, the
environment SHALL report the scope that most recently finished. An update routed with no scope
open at all — fed through the dispatcher directly rather than through the environment — SHALL
become a finished scope of its own rather than being discarded or added to the previous one.

The environment SHALL also provide an assertion spelled directly against this diagnosis,
matched by a substring of the winning handler's qualified name, which SHALL scan **every**
record of the current scope — not only the most relevant one — and SHALL fail naming where
every one of them actually went, including any captured exception, rather than only stating
that the named handler did not run.

#### Scenario: A handled update names its handler and router

- **WHEN** a registered handler runs to completion for a fed update
- **THEN** the report says the update was handled and names the winning handler's qualified
  name and its router

#### Scenario: An update lost in a middleware is distinguished from one that reached a handler

- **WHEN** a middleware returns without calling the next handler in the chain
- **THEN** the report says the update was handled, since something other than "unhandled"
  came back, while naming no handler at all — the field that answers whether anything
  actually ran

#### Scenario: A catch-all handler is named rather than confused with the intended one

- **WHEN** a more specific handler's filter does not match and a catch-all handler runs
  instead
- **THEN** the report names the catch-all handler and its router, not the one the test
  expected

#### Scenario: An exception a bot's own error handler swallows is still captured

- **WHEN** a handler raises and the bot's own error handler returns a value instead of
  re-raising
- **THEN** the report still carries the original exception, captured at the handler that
  raised it, even though the trigger call itself returned normally

#### Scenario: A trigger producing several updates is diagnosed as one scope

- **WHEN** a single actor trigger delivers two updates — a membership transition and the
  chat's own announcement of it — and a handler claims one of the two while ignoring the
  other
- **THEN** both updates appear in the scope's records, and the most-relevant one names the
  update the handler actually claimed rather than whichever of the two finished routing last

#### Scenario: The assertion scans the whole scope, not only the most recent update

- **WHEN** a test asserts the current scope was handled by a name that matches only one of
  several updates fed within it
- **THEN** the assertion succeeds by finding that record among the scope's records, and a
  failure names every record in the scope, not only the last one

#### Scenario: The assertion fails naming where the update actually went

- **WHEN** a test asserts the update was handled by a name that does not match the winning
  handler
- **THEN** the failure names the handler and router that actually claimed it, including any
  captured exception

#### Scenario: A swallowed exception outranks a later update that went fine

- **WHEN** one update of a scope is handled normally and another raises an exception the
  bot's own error handler swallows
- **THEN** the most-relevant record is the one carrying the exception, so an assertion on
  "was this handled" reports the failure rather than the update that worked

#### Scenario: The report resets between scopes

- **WHEN** a second trigger is fed after a first one was handled
- **THEN** the report reflects only the second trigger's scope, not anything left over from
  the first

#### Scenario: Concurrent triggers keep separate scopes

- **WHEN** two updates are fed concurrently, each inside a scope opened by its own task
- **THEN** each scope holds exactly its own record, neither erases the other's, and each
  task reading the report inside its own scope sees only what it fed

#### Scenario: An unrelated feed is not absorbed by a scope another task holds open

- **WHEN** one task holds a scope open while another task, running concurrently, feeds an
  update of its own
- **THEN** the second update forms a scope of its own rather than joining the open one

#### Scenario: A second environment fed from the first one's handler opens its own scope

- **WHEN** a handler of one environment feeds an update to a second environment
- **THEN** the second environment opens a scope of its own for it, rather than treating the
  first environment's in-flight update as a scope of its own to append to

### Requirement: Supported event triggers

The toolkit SHALL provide a trigger for **every** `Update` variant the framework defines,
with no exemptions, so no registered handler is unreachable from a test. This includes the
conversational kinds — sending and editing messages, sending media and captions, pressing
an inline keyboard button, answering an inline query, and chat member transitions —
channel posts and their edits, chosen inline results, shipping and pre-checkout queries,
purchased paid media, chat join requests, chat boosts and their removal, guest messages,
managed bot updates, subscription updates, and additionally poll updates, poll answers,
message reactions and message reaction counts. Each trigger SHALL produce an update
indistinguishable in shape from one Telegram would deliver.

#### Scenario: Pressing an inline keyboard button

- **WHEN** a user actor clicks a button of a message previously sent by the bot
- **THEN** a `callback_query` update is dispatched whose `data` and `message` come from
  the real button and the real stored message

#### Scenario: Chat member transition

- **WHEN** a user actor joins a group chat
- **THEN** a `chat_member` update with correct `old_chat_member` / `new_chat_member`
  statuses is dispatched, and the environment's membership state reflects the new status

#### Scenario: Editing a message sent by a user

- **WHEN** a user actor edits a message it previously sent
- **THEN** an `edited_message` update is dispatched and the stored message content changes

#### Scenario: Every update kind is reachable

- **WHEN** the framework defines an `Update` variant
- **THEN** the toolkit exposes a trigger producing it, and a test asserting this over the
  full set of variants passes with no exemptions declared

#### Scenario: Stopping a draft's generation

- **WHEN** a user actor triggers `stopped_message_generation`
- **THEN** the update is about that user's own private chat with the bot, the only chat
  type `sendMessageDraft` targets, so the dispatcher resolves the event user to the actor,
  and an actor bound to a topic of that chat reports the topic's thread
- **AND** an actor bound to any other chat raises a setup error instead of producing an
  update Telegram never sends

#### Scenario: Posting to a channel

- **WHEN** a post is made to a chat declared as a channel
- **THEN** a `channel_post` update is dispatched rather than a `message` update, and the
  post is stored in that chat

### Requirement: Membership triggers post the group's own join announcement

In a chat type Telegram itself shows the announcement in — a group or a supergroup — the
join and add-bot triggers SHALL also produce the `new_chat_members` service message a real
join or add delivers alongside the membership update, **after** the membership update,
matching the order Telegram's own clients display the two in. This SHALL be suppressible
per call, reverting to the previous single-update behavior. A chat type with no concept of
being "added to" — a private chat — SHALL NOT receive this service message regardless of
the setting, and a trigger that changes membership away rather than into a chat SHALL be
unaffected either way. The trigger's own return value SHALL stay the membership update's
handler result regardless of whether the service message was produced.

#### Scenario: Adding the bot to a group also posts the announcement

- **WHEN** a user actor adds the bot to a group or supergroup
- **THEN** a `my_chat_member` update is dispatched, and a `new_chat_members` message
  carrying the bot is appended to the chat after it

#### Scenario: A regular join also posts the announcement

- **WHEN** a user actor joins a group or supergroup
- **THEN** a `chat_member` update is dispatched, and a `new_chat_members` message carrying
  that user is appended to the chat after it

#### Scenario: The announcement is suppressible

- **WHEN** a join or add-bot trigger opts out of the service message
- **THEN** only the membership update is dispatched, and no message is appended to the chat

#### Scenario: A private chat never gets the announcement

- **WHEN** a user actor with no group binding triggers the equivalent of joining
- **THEN** no `new_chat_members` message is produced, regardless of the setting

#### Scenario: Leaving and removing the bot are unaffected

- **WHEN** a user actor leaves a group, or removes the bot from one
- **THEN** no `new_chat_members` message is produced

### Requirement: Actors can promote and demote chat members

Beyond the raw `promoteChatMember` call, an actor SHALL be able to promote or demote a
member directly, defaulting to promoting or demoting the bot itself — the case almost
every group bot test needs first — and otherwise accepting a declared user, a resolved
state, or a bare id as the subject. Promoting SHALL grant exactly the rights named and no
others, following the same whole-mask rule as the underlying call, but SHALL still promote
even when **no** right is named, unlike a bare call in which naming no right reads as a
demotion — there is no way through this trigger to "explicitly grant nothing." A right that
is not a field of the rights model SHALL be rejected immediately, naming the fields that do
exist, rather than being silently granted to nobody. Demoting SHALL drop the subject to a
plain member and clear both the granted rights and the custom title, while leaving the
subject's tag untouched. Both SHALL refuse to act on the chat's owner as a setup error
rather than as a modeled API rejection, since a trigger arranges the world directly and asks
nothing of the intercepted call path. Both SHALL accept dispatcher data through a
keyword-only parameter distinct from the rights, so that naming a right and passing
dispatcher data are never in conflict with each other on either trigger.

#### Scenario: Promoting with no subject promotes the bot

- **WHEN** an actor calls the promotion trigger with no subject and at least one right
- **THEN** the bot's own membership becomes administrator, carrying exactly the rights named

#### Scenario: Promoting with no rights at all still promotes

- **WHEN** an actor calls the promotion trigger naming no rights
- **THEN** the subject becomes an administrator with every right denied, rather than being
  read as a demotion

#### Scenario: An unknown right is rejected at the call site

- **WHEN** an actor calls the promotion trigger naming a keyword that is not a field of the
  rights model
- **THEN** the call raises immediately, naming the fields that do exist, rather than
  promoting the subject with the misspelled right silently denied

#### Scenario: Demoting clears rights and the custom title but keeps the tag

- **WHEN** an administrator with a custom title and a tag is demoted
- **THEN** the resulting membership is a plain member with no rights and no custom title,
  and the tag is unchanged

#### Scenario: The owner cannot be promoted or demoted through this trigger

- **WHEN** the promotion or demotion trigger names the chat's owner as the subject
- **THEN** the call raises the same refusal `promoteChatMember` gives for its owner, and the
  owner's membership is unchanged

### Requirement: Sending replies is directly expressible

The send trigger SHALL accept a reply target — the message itself, or the id of one already
stored in the actor's chat — that sets the produced message's `reply_to_message`, and the
actor SHALL provide a reply trigger that is this same thing spelled as what it is. An
explicit `reply_to_message` given directly to the send trigger's other field overrides SHALL
still win, matching how those overrides win over every other field.

#### Scenario: Replying by message object

- **WHEN** an actor replies to a `Message` object already stored in its chat
- **THEN** the produced message's `reply_to_message` is that same stored object

#### Scenario: Replying by id resolves through the actor's own chat

- **WHEN** an actor replies to the id of a message already stored in its chat
- **THEN** the produced message's `reply_to_message` is the chat's own stored object under
  that id, not a copy of it

#### Scenario: An explicit field override still wins

- **WHEN** a send trigger is given both a reply target and an explicit `reply_to_message`
  field override
- **THEN** the field override is what the produced message carries

### Requirement: A misdirected click names where the button actually is

When a click trigger cannot find the named `callback_data` on any message in the actor's
own chat, and a button with that same `callback_data` exists on a message in some *other*
chat this world knows about, the failure SHALL name that chat instead of reading identically
to a click on `callback_data` that does not exist anywhere — the two are easy to conflate, a
forgotten chat binding looking exactly like a genuine typo otherwise.

#### Scenario: The failure names the chat that actually has the button

- **WHEN** an actor clicks a `callback_data` that exists on a button in a different chat
  than the one the actor is bound to
- **THEN** the failure names that other chat and points at binding the actor to it

#### Scenario: No hint is given when the button exists nowhere

- **WHEN** an actor clicks a `callback_data` that does not exist on any message in any chat
  this world knows about
- **THEN** the failure does not claim the button exists in some other chat

### Requirement: Deep-link buttons can be followed

A user actor SHALL be able to follow a `url` button that deep-links to the bot under test,
with the same validation a callback button gets: the button SHALL have to be carried by a
message the environment actually holds, either a named one or any message of the actor's
chat. Following SHALL replay what tapping causes in a real client — the user's private chat
with the bot receives `/start <payload>`, or a bare `/start` when the link carries none — so
filters, the command parser, middlewares and FSM all run as they do in production.

Which parsed slot of a link names "the bot" depends on the link's kind, not on a fixed
position: for every kind that addresses a bot by username, the button matches this bot when
that username is the bot's own. The attachment-menu link is the one documented exception —
`t.me/<chat>?attach=<bot>` addresses the *chat* in its username slot and names the bot in the
`attach` parameter instead — so the button matches this bot when that parameter is, and the
automatic scan surfaces such a button as this bot's the same way it surfaces a username match.
A kind that addresses neither a username nor a parameter at any bot — a boost, an invite, a
message link — never matches any bot, so a button of that kind is never treated as this bot's
by either an explicit target or the scan.

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

#### Scenario: An attachment-menu link matches by its parameter, not its address

- **WHEN** the button's url addresses a chat by username and carries `?attach=<bot>` naming
  this bot
- **THEN** the button is treated as this bot's — refused as an attachment-menu link, not as a
  link to a different bot — and the automatic scan surfaces it as a candidate

### Requirement: Only start links are followed, and the rest are refused by name

The toolkit SHALL classify every `t.me` / `telegram.me` / `tg://resolve` url, and every other
`tg://<host>` url, into the kind Telegram documents at https://core.telegram.org/api/links —
one policy per kind, not one bucket for "recognized" and another for "everything else". `start`
SHALL be the only followable kind, including a link with no query, which SHALL parse as a plain
start with no payload. A `start` payload with a non-empty value SHALL be honored alongside any
other query parameter, since a real client reads the parameter it recognizes and ignores the
rest; that precedence SHALL hold in either query order, so a link carrying both a non-empty
`start` and a Mini App, group or channel launch SHALL be followed as the start it also is. An
empty `start` SHALL NOT take this precedence, since it carries no value a real client could
have read as one — `?start=&startapp=y` SHALL classify as the `startapp` link it also is, not
as a bare start, while a bare `?start=` with nothing else in the query is still the plain start
it already was. The precedence SHALL need a real, non-empty `start` to take it, so one of those
kinds appearing alone is refused as before.

A query parameter Telegram documents as also being the companion of another format —
`startapp` and `startattach`, each of which also serves as the start parameter of a named-app
or named-chat attachment-menu link, and `text`, which a public username link may carry as a
prefilled draft alongside another parameter — SHALL NOT outrank the format that carries it:
`?startapp=x&text=y` SHALL classify as the Mini App link `startapp` names, not the draft `text`
would be alone, and `?appname=<name>&startapp=<param>` SHALL classify as the direct Mini App
link `appname` names, with `startapp` read as its parameter. A companion parameter appearing
alone in the query still classifies by the format it names.

Every other documented kind SHALL be refused with a message naming that kind and what a real
client does with it, rather than being replayed as a plain start or lumped into a generic
rejection: group, Mini App, channel and attachment-menu launches; a direct Mini App link and a
game-share link; an affiliate-referral link; a profile link; a prefilled-draft link; chat invite
links (including the legacy `joinchat` path and the `tg://join` form); a phone-number link,
told apart from an invite link by its all-digit tail rather than folded into the same kind; a
message link and its threaded and private-channel forms; a story link; a channel's web-preview
link (`t.me/s/<username>`), distinguished from a direct Mini App link despite sharing the
`t.me/<name>` shape; a share link; an invoice
link, on its `$<slug>`, `/invoice/<slug>` and `tg://invoice` forms alike; a boost link, on its
path, query and `tg://` forms; a video-chat link, including its `livestream` and legacy
`voicechat` query spellings; a business-chat link; a sticker- or emoji-set link; and any Telegram
service link (a proxy, theme, language pack, wallpaper, login code, chat folder or an app
screen). Where the toolkit models the action a link only opens a screen for, the message SHALL
point at the trigger that does: an invoice link SHALL point at `pay()` and `pre_checkout_query()`,
a boost link SHALL point at `boost()`, and a prefilled-draft link SHALL name the text it would
have left unsent and point at `send()` with that text. A `tg://` url whose host is not `resolve`
SHALL still be classified as a Telegram link — by host where the host is one of the documented
ones, and as a service link otherwise — never reported as "not a Telegram link" merely because
its host is unfamiliar. A url that addresses neither a bot nor any other documented Telegram
surface SHALL be refused as not a Telegram link at all.

A `start` payload SHALL be validated against the alphabet Bot API deep linking defines —
`A-Z`, `a-z`, `0-9`, `_` and `-`, 1 to 64 characters — before being followed. A payload outside
that alphabet SHALL be refused naming the rule, rather than delivered to the handler, since a
real client never sends `/start` for a link its own payload makes invalid. The caller MAY opt
out of this validation, since the Bot API states the rule for what a bot should put in a link
but does not promise a client enforces it, and production bots do receive payloads outside it;
opting out SHALL replay the payload exactly as the button carries it, and SHALL NOT change
which kinds are followable — a `startapp` link opted out of payload validation is still refused
as a Mini App link, not silently followed as a start.

#### Scenario: A bare profile link replays as a plain start

- **WHEN** the button's url is `https://t.me/<bot>` with no query
- **THEN** following it sends `/start` with no payload

#### Scenario: An explicit non-empty start wins over a start-ish parameter beside it

- **WHEN** the button's url carries both a non-empty `start` and one of `startapp`,
  `startgroup` or `startchannel`, in either order
- **THEN** following it sends `/start` with the `start` payload rather than being refused

#### Scenario: An empty start does not win over a start-ish parameter beside it

- **WHEN** the button's url carries `?start=` with an empty value alongside `startapp`,
  `startgroup`, `startchannel`, `startattach` or `attach`, in either order
- **THEN** following it raises as that other kind, rather than sending a bare `/start`

#### Scenario: A companion parameter does not outrank the format that carries it

- **WHEN** the button's url carries a companion parameter (`startapp`, `startattach` or `text`)
  alongside a parameter of another documented format, in either order
- **THEN** following it raises as that other format, not as the companion's own kind

#### Scenario: Every documented format is refused as the format it is

- **WHEN** the button's url is one of the link forms https://core.telegram.org/api/links
  documents — a direct Mini App link, a message link, a story link, a share link, an invoice
  link, a boost link, a video-chat link, a business-chat link, a sticker-set link, a
  prefilled-draft link, an affiliate-referral link, a profile link, or a service link such as a
  proxy or language pack
- **THEN** following it raises, naming that kind and what a real client does with it, and — for
  an invoice or a boost link — pointing at the trigger (`pay()`, `pre_checkout_query()`,
  `boost()`) that models the underlying action instead

#### Scenario: A channel web-preview link is not mistaken for a Mini App

- **WHEN** the button's url is `t.me/s/<username>`, `t.me`'s own web preview of a channel's
  posts
- **THEN** following it raises naming it a channel web-preview link, not a direct Mini App link
  of a bot named `s`

#### Scenario: A phone link is not mistaken for an invite link

- **WHEN** the button's url is `t.me/+<digits>` or `tg://resolve?phone=<digits>`
- **THEN** following it raises naming it a phone-number link, and the message does not call it
  an invite link

#### Scenario: A `tg://` host other than `resolve` is still a Telegram link

- **WHEN** the button's url is a `tg://` url whose host is not `resolve`, whether or not the
  toolkit enumerates that host by name
- **THEN** following it raises naming the kind that host documents, or naming it a Telegram
  service link when the host is not individually enumerated — never claiming the url is not a
  Telegram link

#### Scenario: An unsupported kind is named, not downgraded

- **WHEN** the button opens a group chooser, a Mini App, a channel chooser or the attachment
  menu, with no `start` beside it
- **THEN** following it raises, naming that kind and what to do instead, rather than sending
  a plain `/start`

#### Scenario: A start payload outside the deep-linking alphabet is refused

- **WHEN** the button's `start` payload is longer than 64 characters, percent-encoded, or
  otherwise outside `A-Z`, `a-z`, `0-9`, `_` and `-`
- **THEN** following it raises naming the deep-linking payload rule, and no `/start` is sent to
  the handler

#### Scenario: Payload validation can be dropped to reproduce what a client actually delivered

- **WHEN** the caller opts out of `start` payload validation and the button's payload is
  outside the deep-linking alphabet
- **THEN** the payload is replayed exactly as carried, and a kind other than `start` is still
  refused rather than made followable

#### Scenario: An unrecognized query is refused rather than guessed

- **WHEN** the button's url carries a query parameter none of the documented kinds define
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
actor sends, when an actor binds to its own id, and when the environment's own chat accessor
is asked for the id of a *declared user* whose private chat was not itself declared. Any
*other* chat the blueprint never declared SHALL still be refused, since the world cannot
invent a group's title, type or membership from an identifier.

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

#### Scenario: The environment's chat accessor opens it too

- **WHEN** a test asks the environment's chat accessor for the id of a declared user whose
  private chat was never declared or opened
- **THEN** the chat is opened and returned, agreeing with what the actor path already does
  for that same id

#### Scenario: An undeclared group is still refused

- **WHEN** an actor binds to the identifier of a group nobody declared
- **THEN** the call raises, because the world has nothing to build that chat from

#### Scenario: The bot writing first does not open one

- **WHEN** a handler sends a message to a declared user whose private chat was never declared
  and never opened
- **THEN** the call raises rather than opening the chat, because a real bot cannot start the
  conversation

### Requirement: Modeled Bot API methods mutate world state

Bot API calls made by handlers SHALL be intercepted. For methods the environment models,
the call SHALL be applied to the world state and SHALL return a result consistent with
that state. Modeled methods SHALL cover at minimum: sending messages and media, sending
invoices, games, paid media, checklists and rich messages, editing message text, caption,
reply markup, media, live location and checklist, deleting messages, forwarding and
copying messages singly and in batches, pinning, unpinning and unpinning all, answering
callback queries, and chat member administration.

#### Scenario: Sending a message appends it to the chat

- **WHEN** a handler calls `message.answer("Welcome!")`
- **THEN** a new `Message` appears in that chat's message list with the bot as sender, a
  unique `message_id`, and the resolved text

#### Scenario: Editing mutates the stored message

- **WHEN** a handler edits the text of a message the bot sent earlier
- **THEN** the stored message's text changes in place, and no additional message is added
  to the chat

#### Scenario: Deleting removes the message

- **WHEN** a handler deletes a message
- **THEN** the message is no longer present in the chat's message list, and a later
  attempt to edit it fails with the same error Telegram would return

#### Scenario: Bot-level defaults are applied before state is recorded

- **WHEN** the environment's bot declares `parse_mode="HTML"` and a handler sends a
  message without an explicit `parse_mode`
- **THEN** the recorded call and the stored message carry the resolved default

#### Scenario: Every message-producing method stores its message

- **WHEN** a handler calls `sendInvoice`, `sendGame`, `sendPaidMedia`, `sendChecklist`,
  `sendLivePhoto` or `sendRichMessage`
- **THEN** a `Message` carrying the corresponding payload field appears in the chat with a
  unique `message_id`, and the returned object is that stored message

#### Scenario: A button on any sent message is clickable

- **WHEN** a handler sends an invoice or a rich message carrying an inline keyboard, and a
  user actor clicks one of its buttons
- **THEN** the button is resolved from the stored message, exactly as it is for a message
  sent with `sendMessage`

### Requirement: Unmodeled methods are recorded and answered

Any Bot API method the environment does not model SHALL still succeed by default: the
call is recorded and answered with a schema-valid result synthesized from the method's
declared return type. Synthesis SHALL derive from the generated method and type metadata,
so newly added Bot API methods work without changes to the toolkit.

The set of methods that are deliberately left unmodeled SHALL be enumerated rather than
implied, and SHALL distinguish surfaces that are record-only by decision from clusters
whose modeling is merely deferred.

#### Scenario: A method with no state semantics returns a valid object

- **WHEN** a handler calls a method the environment does not model and whose return type
  is a Bot API object
- **THEN** the call returns an instance of that type with all required fields populated,
  and the call is visible in the call log

#### Scenario: A newly added Bot API method needs no toolkit change

- **WHEN** the framework gains a new generated method and a handler calls it
- **THEN** the call succeeds with a synthesized result without any update to the testing
  package

#### Scenario: A record-only method is never also modeled

- **WHEN** the enumerated record-only surface is compared against the modeled method
  registry
- **THEN** the two do not overlap, so modeling one of those methods requires removing it
  from the record-only list in the same change

### Requirement: Per-test overrides of API results

A test SHALL be able to override the outcome of a specific method for that test only —
returning a chosen result or raising a Telegram error — and the override SHALL take
precedence over both modeling and synthesis. Overrides SHALL be scopable to a number of
calls so that consecutive calls can return different outcomes.

An override declaration SHALL be narrowable to calls of a particular shape: equality tests
on named fields of the **resolved** method — after bot-level defaults are filled in — ANDed
together, plus an arbitrary predicate for what field equality cannot say. Declaring a filter
on a field the method does not have SHALL be rejected immediately rather than registering a
rule that can never match. When more than one declared rule could answer a call, the rules
SHALL be tried in the order they were declared and the first whose shape accepts the call
SHALL win; a rule whose shape does not accept a call SHALL be left untouched by it, including
its remaining-calls budget, so an earlier call to a *different* shape cannot exhaust it.

Every override declaration SHALL return a handle that withdraws exactly the rules that
declaration registered, independently of any other declared override, and that handle SHALL
also work as a context manager scoping the override to one block.

The environment SHALL provide a named recipe for making every call addressed at one party
fail the way a real block does, under the same handle-and-scoping rules as a general
override but carrying no call-count budget — it SHALL hold for as long as it is in force
rather than for a fixed number of calls. This SHALL cover every method that delivers content
into a chat, **and** every method that acts on content already in that chat instead of
delivering into it, since a bot's own recovery path for a failed delivery — editing,
(un)pinning, or setting *and clearing* a reaction on what it already sent — must be seen to
fail there too; the
environment MAY name specific methods it deliberately excludes from this recipe, documenting
why, without that exclusion being a defect. The party SHALL be matchable however a call
addresses it, including by an addressing field other than the one primarily used to declare
the block, so that "this recipient" is caught whichever field the intercepted call happens
to name it with — but only where that field names the **addressee**: a field that names some
other participant of a chat the call addresses separately SHALL NOT be treated as naming the
blocked party, so an operation the bot performs in a chat it can still reach is not refused
merely because it mentions the blocked user. Wherever a call's shape includes a chat-addressing field that Telegram
allows to be given either by numeric id or by `@username`, an override's declared value and
the call's actual value SHALL both be resolved through the world before comparison, so a
rule declared with one spelling still answers a call made with the other.

A call SHALL be recorded in the call log **before** any override is consulted for it, so
that a test can assert both that the call was made — reaching the right addressee with the
right content — and separately assert on how an override answered it.

The environment SHALL provide an assertion that every override currently declared on it has
answered at least one call, failing by naming each one that has not — the single most common
reason a bot behaves as though a declared override were never registered at all. The same
naming SHALL be appended to a wait's timeout message, since a never-matched override is
frequently the reason the awaited condition never became true.

Only rules a test declared as **expectations** SHALL be reportable that way. A rule generated
as one alternative of a *simulation* — the set of methods the blocked-party recipe refuses,
of which a bot is expected to take one or two and leave the rest untouched — SHALL be excluded
from both the assertion and the timeout listing entirely, whether or not any of that
simulation's rules ever fired, since a simulation is not a prediction of which alternative the
bot will take. An expectation declared alongside a simulation SHALL still be reported.

#### Scenario: Overriding a result

- **WHEN** a test declares that `GetChatMember` returns a specific member object
- **THEN** every call to that method in that test returns it, regardless of world state

#### Scenario: Simulating a Telegram failure

- **WHEN** a test declares that `SendMessage` raises `TelegramForbiddenError`
- **THEN** the handler observes that exception exactly as it would in production, and the
  chat state is unchanged

#### Scenario: Overrides do not leak between tests

- **WHEN** one test overrides a method and a later test in the same module does not
- **THEN** the later test observes the default modeled or synthesized behavior

#### Scenario: Two recipients of one trigger are given independent outcomes

- **WHEN** a test declares one outcome for `SendMessage` filtered to one chat id and another
  outcome filtered to a second chat id, and a handler messages both chats from one trigger
- **THEN** each call is answered according to the rule that names its own chat id, regardless
  of which of the two the handler happens to call first

#### Scenario: A rule that does not match is not consumed

- **WHEN** a call-limited rule is declared for one chat id, and a call is made against a
  *different* shape before a call matching the rule arrives
- **THEN** the non-matching call does not reduce the rule's remaining budget

#### Scenario: A filter on an unknown field is rejected at declaration time

- **WHEN** a test declares a field filter naming a field the method does not have
- **THEN** the declaration raises immediately, naming the fields that do exist, rather than
  registering a rule that can never match

#### Scenario: A handle withdraws only what it declared

- **WHEN** a test cancels the handle one override declaration returned
- **THEN** only the rules that declaration registered are withdrawn, and every other
  declared override is unaffected

#### Scenario: An override is scoped to a block

- **WHEN** a test uses an override's handle as a context manager around a trigger
- **THEN** the override answers calls made inside the block, and calls made after the block
  observe the default behavior again

#### Scenario: Every delivery method into a blocked chat fails

- **WHEN** a test declares the blocked-chat recipe for one chat id
- **THEN** sending, forwarding and copying into that chat all fail the way a real block fails
  them, while the same call into a *different* chat still succeeds

#### Scenario: Acting on content already in the blocked chat also fails

- **WHEN** a test declares the blocked-chat recipe for one chat id, and the bot then edits,
  pins, reacts to, or *clears its reaction from* a message already stored in that chat
- **THEN** each of those calls fails the same way a delivery into that chat fails

#### Scenario: A field naming someone other than the addressee does not trigger the recipe

- **WHEN** a test declares the blocked-chat recipe for one party, and the bot then makes a
  call addressed at a *different*, reachable chat that merely mentions the blocked party
  through a field naming whose content is acted on
- **THEN** that call succeeds, since a block stops what the bot does in the blocked party's
  own chat rather than everything that mentions them

#### Scenario: A deliberately excluded method is unaffected by the recipe

- **WHEN** a test declares the blocked-chat recipe for one chat id, and the bot then calls a
  method the recipe documents as excluded
- **THEN** that call succeeds, and a test that wants it to fail declares that outcome itself

#### Scenario: A party addressed by a different field is still caught

- **WHEN** a test declares the blocked recipe for one party, and a call the bot makes
  addresses that same party through a field other than the one the recipe was declared
  against
- **THEN** that call still fails the way the recipe intends

#### Scenario: Two recipients can be blocked independently

- **WHEN** a test declares the blocked-chat recipe for two different chat ids at once
- **THEN** both chats' deliveries fail, and a message to a third, unblocked chat still
  succeeds, regardless of which chat a handler happens to message first

#### Scenario: An addressing field is matched by either of its spellings

- **WHEN** a call's chat-addressing field allows both a numeric id and an `@username`, and an
  override or the blocked-chat recipe is declared against one spelling
- **THEN** a call made with the other spelling of the same chat still matches, in both
  directions

#### Scenario: A refused call is still visible in the call log

- **WHEN** a call is answered by an override that raises
- **THEN** the call log still holds the call as the code under test built it, so a test can
  assert on the addressee and content of a call that was refused

#### Scenario: A never-fired override is named

- **WHEN** a test declares an override whose shape never matches any call made during the
  test, and then asks whether every declared override fired
- **THEN** the assertion fails, naming that override, rather than the test passing silently
  while the bot behaved as though the override did not exist

#### Scenario: A simulation's untaken alternatives are not reported as never-fired

- **WHEN** a test runs inside the blocked-chat recipe's scope, where the bot takes one or two
  of the methods the recipe refuses and never calls the rest, and then asks whether every
  declared override fired — or a wait inside that scope times out
- **THEN** neither the assertion nor the timeout mentions the recipe's untaken alternatives,
  while an expectation the test declared by hand alongside it is still named if it never fired

#### Scenario: A never-fired override is named in a wait's timeout

- **WHEN** a test declares an override that never matches any call, and a wait started after
  it times out
- **THEN** the timeout message also names that override

### Requirement: Call log for request assertions

The environment SHALL record every intercepted call in order and expose typed queries
over them — the last call of a type, all calls of a type, the total count, and filtering
by predicate. Recorded entries SHALL be the actual `TelegramMethod` objects, with defaults
already resolved.

#### Scenario: Asserting on the last request of a type

- **WHEN** a test asks the call log for the last `SendMessage`
- **THEN** it receives the method object whose fields can be asserted directly

#### Scenario: Asserting that a method was never called

- **WHEN** a test asserts the count of a method type is zero
- **THEN** the assertion reflects the calls made during that test only

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
This ownership SHALL be enforced per chat, not only when the whole mapping is replaced, so
that no path into the registry — a whole-mapping assignment, an item assignment, or any of
the mapping protocol's own bulk-update operations — can register a chat that already belongs
to a *different* world without the same refusal. Registering a **fresh** chat, one that does
not yet belong to any world, SHALL always succeed: a plain mapping assigned wholesale SHALL be
wrapped into a fresh registry wired to this world, and a bare `ChatState` SHALL be adopted the
same way wherever it is registered. Registering a chat that already belongs to *this* same
world SHALL be a no-op, so re-assigning a world's own `chats` to itself, or re-registering a
chat under the id it already holds, changes nothing. Registering a chat that belongs to a
*different* world SHALL instead be refused, because a chat is not a copy the registry could
safely adopt: rewriting which world it belongs to would rewrite `chat.world` on the very
object the donor world still holds onto, silently binding the donor's own chat — and
everything it stores afterwards — to this world's bot instead, while the donor itself
observes nothing was ever reassigned. Moving a chat to a different world SHALL remain
possible, said explicitly: detaching it from its current world first, so that it is
registered here as the fresh chat it has been made to be, is one way; handing over an
independent copy of it, or one rebuilt from the same declaration, are others — none of which
require the registry itself to guess which one a test meant.

The refusal SHALL name remedies that **work as written**: every remedy it offers SHALL be
spelled with the detaching step included, since a chat obtained from a declaration or a copy
of the world is itself owned by the world it came from and would otherwise land the reader on
the same refusal again. The whole-mapping refusal SHALL likewise point at building the world
that is wanted and using it whole, rather than at any form of transplanting chats between
worlds — including the unwrapped plain mapping, which is refused chat by chat for the same
reason.

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

#### Scenario: Assigning another world's live registry is refused

- **WHEN** a test assigns one world's live chat registry to another world's `chats` attribute
- **THEN** the assignment raises, naming the ownership rule, and the donor's own chats stay
  wired to the donor and bound to the donor's bot

#### Scenario: Unwrapping a foreign registry into a plain mapping does not bypass the refusal

- **WHEN** a test assigns a plain `dict` built from one world's chats — `dict(other.chats)` —
  to another world's `chats` attribute
- **THEN** the assignment raises the same way, because each chat inside it still belongs to
  the donor world, and the donor's own chats stay wired to the donor

#### Scenario: A chat detached from its world can be moved

- **WHEN** a test removes a chat from its current world's registry, marks it as belonging to
  no world, and then registers it in a different world
- **THEN** the registration succeeds, and the chat is now wired to the new world alone

#### Scenario: Every remedy a refusal names actually runs

- **WHEN** a test takes the code the refusal message recommends and runs it exactly as
  printed
- **THEN** the destination world ends up holding a correctly wired chat, rather than the same
  refusal being raised by the very line the message recommended

#### Scenario: A fresh chat is adopted normally

- **WHEN** a test registers a `ChatState` that has never belonged to any world
- **THEN** the registration succeeds and the chat is wired to the registering world

#### Scenario: Re-registering a chat in its own world is a no-op

- **WHEN** a test registers a chat under a world it already belongs to
- **THEN** the chat's wiring is unchanged

### Requirement: Handlers receive the world's own objects

An update SHALL arrive at the dispatcher already bound, so that the framework does not
re-create it and the object a handler receives is the object the world stores. An update
carrying objects that belong to a *different* environment SHALL be copied instead of
claimed, and the message it carries SHALL be registered in the destination chat.

Registering a carried message whose id is already taken by a *different* message in the
destination chat SHALL raise `WorldLookupError` naming both messages, rather than silently
keeping the one already there — a handler reacting to the incoming update would otherwise work
on a message the world never stores, and a `wait_for_message` waiting for it would wait
forever with nothing to explain why. Registering one whose id is taken by an equal message —
the same update fed again, or an equal one built the same way twice — SHALL stay the silent
no-op it always was.

#### Scenario: Identity survives the dispatcher

- **WHEN** a user actor sends a message and the handler records the `Message` it received
- **THEN** that object is the very one the chat's message list holds

#### Scenario: An update built for another environment does not act on it

- **WHEN** one update object is fed to two environments
- **THEN** the second environment answers in its own world, and the reply it sends does not
  reuse the incoming message's identifier

#### Scenario: A carried message id colliding with a different message is refused

- **WHEN** an update carries a message whose id is already taken in the destination chat by a
  message with different content
- **THEN** registering it raises `WorldLookupError` describing both the message already there
  and the incoming one, rather than silently discarding the incoming one

#### Scenario: Re-registering an equal carried message is still a no-op

- **WHEN** an update carrying a message equal to one already registered under the same id is
  fed again
- **THEN** no error is raised and the chat's state is unchanged

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

### Requirement: Telegram errors behave like production errors

A call the real Bot API would refuse SHALL fail the way it fails in production: the
framework's own exception types from `aiogram.exceptions`, raised through the session's own
response check, carrying Telegram's wording — whether the refusal comes from a modeling rule,
from a declared override, or from an invalid operation such as editing a deleted message. So
an `except` branch in the bot under test is exercised exactly as it would be against real
Telegram.

#### Scenario: Invalid operation raises a framework exception

- **WHEN** a handler edits a message that no longer exists
- **THEN** `TelegramBadRequest` is raised with a description explaining the failure

#### Scenario: Registered error handlers receive the exception

- **WHEN** the dispatcher has an error handler and an intercepted call raises
- **THEN** the error handler runs through the normal dispatcher error pipeline

#### Scenario: A handler can catch the refusal itself

- **WHEN** a handler wraps a call in `except TelegramBadRequest`
- **THEN** it catches the refusal and reads Telegram's own wording out of it

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

The condition wait SHALL accept one view to watch, or an iterable of several, named by
declaration, by resolved chat or topic state, by a **user** — standing for that user's private
chat with the bot, opened on demand exactly as the actor path opens it — or by bare chat id,
mixed freely — the same
vocabulary every waiting helper that names a chat or topic accepts — whose contents are
appended to the timeout message when it gives up — because the condition is a lambda over
state the failure cannot otherwise describe, while what the bot posted instead is usually
the answer. The timeout message SHALL also name any override declared on the environment
that has not yet answered a call, since a never-matched override is frequently the reason
the condition never became true.

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

#### Scenario: A watched chat's contents appear in a timeout

- **WHEN** a condition wait names a chat or topic to watch and times out
- **THEN** the failure message includes that chat or topic's messages, in addition to the
  condition's own description

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

### Requirement: Waiting for a message across several chats at once

The environment SHALL provide a wait that polls several views together and returns once
**every** one of them holds a matching message, rather than requiring a test to await each
view's own message wait in turn. It SHALL accept the same vocabulary a single condition
wait's `watch=` accepts for naming what to watch — a declaration, a resolved chat or topic
state, a user standing for their private chat with the bot, or a bare chat id, one on its own
or any iterable of them mixed freely — so that a
broadcast confined to one topic of a forum is expressible the same way a broadcast across
whole chats is, and so that the broadcast this helper exists for — every player got their
message — is written with the list of user declarations a test already holds. It SHALL apply the same newest-match rule a single view's own message wait
applies, and a predicate that raises on a message SHALL count as "no match" for that message
exactly as it does for a single view's own wait, with what it raised reported per view once
the wait gives up. A timeout SHALL name only the views still missing a match, not the ones
that already have one.

#### Scenario: A broadcast wait returns once every chat has a match

- **WHEN** a handler messages several chats from one trigger and a test waits across all of
  their ids at once
- **THEN** the wait returns a result keyed by chat id, once every named chat holds a message
  satisfying the predicate

#### Scenario: Mixed forms of naming a chat are accepted

- **WHEN** the chats passed to the broadcast wait mix a blueprint declaration, a resolved
  chat state and a bare id
- **THEN** all three resolve to their chats and are waited on together

#### Scenario: A list of users names their private chats

- **WHEN** a broadcast wait is given the user declarations a blueprint handed back, for users
  whose private chats were never declared
- **THEN** each user's private chat is opened and waited on, so the documented "every player
  got the message" broadcast is written with the objects the test already holds

#### Scenario: A broadcast wait can be confined to a topic

- **WHEN** the views passed to the broadcast wait include a forum topic rather than a whole
  chat
- **THEN** a match is required only among that topic's own messages, not the whole forum's

#### Scenario: A raising predicate is reported per view on timeout

- **WHEN** the predicate raises on a message in one of the watched views and the wait times
  out
- **THEN** the failure reports what the predicate raised for that view, the same way a single
  view's own wait reports it

#### Scenario: A timeout names only the chats still missing a match

- **WHEN** some but not all of the named chats already hold a matching message and the wait
  times out
- **THEN** the failure names only the chats that never got one, not the ones that did

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

Every waiting helper SHALL fail with a `WaitTimeoutError`, which SHALL be a `TimeoutError`,
and its message SHALL name what was awaited and show the state that was there instead — the
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

### Requirement: Background tasks a test leaves running can be drained

The environment SHALL provide an explicit, opt-in way to cancel and await every task the
test itself spawned and left running — a bot's own scheduler or timer — and to report how
many there were. Only tasks created after the environment was built SHALL count as the
test's own; a task already running SHALL be left alone. Because the environment's
construction may happen with no event loop running at all, "already running" SHALL be
established as of this environment's first asynchronous action if that comes later than
construction, so that a task belonging to another, wider-scoped fixture — one already alive
by the time this environment's own tasks could possibly begin — is spared regardless of
whether the environment could observe it at construction time. Where **neither** of those two
moments could observe anything — the environment was built with no loop running and has since
done nothing asynchronous at all — it SHALL be treated as owning no tasks: nothing is
cancelled and the reported number is zero, since every task in the loop would otherwise count
as this environment's own.

A task that does not finish
within a stated timeout after being cancelled SHALL fail loudly rather than being abandoned
a second time. A task that ends with anything other than the cancellation it was sent SHALL
also fail loudly, distinctly from a task that merely failed to finish in time, naming every
such task and preserving the original failure so it can be inspected rather than only
noted. This SHALL hold for a task that ended **before** the drain as much as for one it
cancelled: a task that died of its own bug earlier in the test SHALL be reported the same way,
which requires the environment to remember the tasks created while it is live rather than to
rely on a listing of unfinished ones. Such a task SHALL NOT be counted in the number reported,
which counts what was drained. Where a task that outlived its cancellation and a task that
failed on its own are found together, the unfinished task SHALL be the failure raised, naming
the other alongside it, and the preserved original failure SHALL be attached to whichever
error is actually raised. This SHALL NOT be invoked automatically by environment teardown, since teardown has
both an asynchronous and a synchronous path and an automatic drain would behave differently
between them, and since cancelling tasks a test never mentioned as an invisible side effect
of teardown would obscure a stopped background process as a mystery rather than a stated
outcome.

#### Scenario: Tasks the test left running are cancelled and awaited

- **WHEN** a trigger schedules a background task that is still running when the test asks to
  drain, with a timeout that comfortably exceeds what cancellation takes
- **THEN** the task is cancelled, awaited, and counted in the number returned

#### Scenario: A task present before the environment was built is left alone

- **WHEN** a task was already running before the environment was constructed
- **THEN** draining does not cancel it and does not count it

#### Scenario: A task belonging to a wider-scoped fixture is spared even without a running loop at construction

- **WHEN** the environment is constructed synchronously with no event loop running, a task
  from a wider-scoped fixture is already running by the time this environment first acts
  asynchronously, and the test then asks to drain
- **THEN** draining does not cancel that task, exactly as if it had been running at
  construction

#### Scenario: A task that outlives its cancellation fails loudly

- **WHEN** a task swallows its own cancellation and is still running after the stated
  timeout
- **THEN** draining raises, naming the task, rather than abandoning it silently

#### Scenario: A task that fails on its own is reported rather than silently retrieved

- **WHEN** a drained task ends with an exception of its own rather than with the
  cancellation it was sent
- **THEN** draining raises, naming that task and preserving its original failure, rather
  than treating it the same as a task that was simply cancelled on time

#### Scenario: A task that died before the drain is reported too

- **WHEN** a task spawned during the test raises and finishes on its own well before the
  test asks to drain
- **THEN** draining still raises, naming that task and preserving its failure, rather than
  reporting that there was nothing to drain

#### Scenario: An environment that never acted asynchronously drains nothing

- **WHEN** an environment built with no event loop running is asked to drain before it has
  fed any update or handled any call, while unrelated tasks are running in the loop
- **THEN** nothing is cancelled and the reported number is zero

#### Scenario: Draining is not automatic

- **WHEN** an environment with an uncancelled background task is disposed, synchronously or
  asynchronously, without draining being called
- **THEN** disposal completes without draining the task itself

### Requirement: FSM state is inspectable and settable

The environment SHALL expose the FSM context for any user/chat pair so that a test can
assert the resulting state and data after a flow, and can arrange a starting state
without replaying the whole conversation. Resolution SHALL go through the dispatcher's
configured `FSMStrategy` and SHALL accept the topic and the business connection, so that
the key the environment returns is the same key the dispatcher used for the corresponding
event under every strategy.

#### Scenario: Asserting state after a flow

- **WHEN** a flow drives a user into a specific `State`
- **THEN** the test can read that user's current state and data from the environment

#### Scenario: Arranging a starting state

- **WHEN** a test sets a user's state and data before triggering an event
- **THEN** handlers and scenes observe that state, without the earlier steps being replayed

#### Scenario: Topic-scoped strategies resolve the same key as the dispatcher

- **WHEN** the dispatcher uses a topic-aware `FSMStrategy` and a handler stores data for an
  event triggered inside a topic
- **THEN** asking the environment for that user's state in that topic returns the stored
  data, rather than an empty context for a different key

#### Scenario: Business connections are part of the key

- **WHEN** a handler stores data while processing an event on a business connection
- **THEN** asking the environment for that user's state on the same connection returns the
  stored data

### Requirement: Forum topics are declared and modeled

A blueprint SHALL be able to declare forum topics on a chat, which marks that chat as a
forum. Each topic SHALL own its own thread of messages, and the environment SHALL track a
topic's name, icon and open/closed state.

#### Scenario: Declaring a topic makes the chat a forum

- **WHEN** a blueprint declares a topic on a supergroup
- **THEN** every environment built from it exposes that topic, and the chat reports itself
  as a forum

#### Scenario: Messages belong to their topic

- **WHEN** messages are sent in two different topics of the same chat
- **THEN** each topic's thread contains only its own messages, while the chat still lists
  all of them

### Requirement: Forum methods drive topic state

The forum management methods SHALL be applied to the world instead of being synthesized:
creating, editing, closing, reopening and deleting a topic, unpinning all of a topic's
messages, and the General-topic variants. Each SHALL emit the matching service message
into the chat where Telegram would; closing and reopening the General topic SHALL emit
`forum_topic_closed` and `forum_topic_reopened` with no thread id. A private chat SHALL take
creating, editing and deleting a topic and unpinning its messages, and its topic messages
SHALL carry their thread id; closing a topic there, and the General-topic methods, SHALL
fail with `the chat is not a supergroup forum`.

#### Scenario: Creating a topic

- **WHEN** a handler calls `createForumTopic`
- **THEN** the returned topic exists in the chat with the requested name, and a
  `forum_topic_created` service message appears in the chat

#### Scenario: Closing and reopening a topic

- **WHEN** a handler closes a topic and later reopens it
- **THEN** the topic's state follows, and `forum_topic_closed` and `forum_topic_reopened`
  service messages are appended in order

#### Scenario: Closing the General topic

- **WHEN** a handler closes the General topic
- **THEN** it is closed, and a `forum_topic_closed` message with no thread id is appended

#### Scenario: Editing a topic

- **WHEN** a handler edits a topic's name or icon
- **THEN** the stored topic reflects the change and a `forum_topic_edited` service message
  is emitted

#### Scenario: Deleting a topic

- **WHEN** a handler deletes a topic
- **THEN** the topic and its messages are gone from the chat, and a later attempt to post
  into it fails with `message thread not found`, as the Bot API server answers it

#### Scenario: A topic in a private chat

- **WHEN** a handler creates a topic in a private chat and sends into it
- **THEN** the message carries the topic's thread id, is a topic message, and replies to
  nothing

### Requirement: Actors can be bound to a topic

A user actor SHALL be bindable to a topic of a forum chat, and every update it produces
SHALL carry the topic's thread identifier and be marked as a topic message, so that
handler replies stay inside the topic exactly as they do in production.

#### Scenario: Triggering inside a topic

- **WHEN** an actor bound to a topic sends a message
- **THEN** the update carries that topic's `message_thread_id` and `is_topic_message`, and
  a handler replying with `message.answer(...)` produces a message in the same topic

#### Scenario: Topic binding does not leak

- **WHEN** an actor is bound to a topic
- **THEN** the actor it was derived from remains bound to whatever it was bound to before

### Requirement: Business connections are declared and modeled

A blueprint SHALL be able to declare business connections, each carrying the owning user,
the connection's chat identifier, whether it is enabled, and the bot's rights. The
environment SHALL answer `getBusinessConnection` from that state, and SHALL apply
`readBusinessMessage` and `deleteBusinessMessages` to the world.

#### Scenario: Reading a declared connection

- **WHEN** a handler calls `getBusinessConnection` for a declared connection
- **THEN** it receives the declared owner, rights and enabled flag

#### Scenario: Deleting business messages

- **WHEN** a handler deletes messages on a business connection
- **THEN** those messages are removed from the chat they belonged to

#### Scenario: Unknown connection

- **WHEN** a handler asks for a connection that was never declared
- **THEN** the call fails with `WorldLookupError` — a gap in the blueprint, not a Telegram
  rejection — rather than returning a synthesized connection

### Requirement: Business messages are attributed to the business account

A message sent with a business connection identifier SHALL be stored as sent by the
**business account user**, not by the bot, with the bot recorded as the sending business
bot and the connection identifier carried on the message.

#### Scenario: Sender is the business account

- **WHEN** a handler replies on a business connection
- **THEN** the stored message's sender is the connection's owner, its sending business bot
  is the bot, and its business connection identifier matches the connection

#### Scenario: Ordinary messages are unaffected

- **WHEN** a handler sends a message without a business connection identifier
- **THEN** the stored message is sent by the bot, with no business attribution

### Requirement: Business update triggers

Actors SHALL be able to trigger the business update types: a message on a connection, an
edit of one, a connection being enabled or disabled, and messages being deleted by the
business account.

#### Scenario: Business message reaches its handler

- **WHEN** an actor sends a message on a business connection
- **THEN** the `business_message` handler runs, and the event carries the connection
  identifier

#### Scenario: Connection is disabled

- **WHEN** a connection is disabled through the environment
- **THEN** a `business_connection` update is dispatched whose connection reports itself as
  not enabled, and the declared state follows

#### Scenario: Business messages deleted

- **WHEN** the business account deletes messages
- **THEN** a `deleted_business_messages` update is dispatched listing those message
  identifiers, and the messages are gone from the chat

### Requirement: Communities are declared and triggered

A blueprint SHALL be able to declare a community and attach chats to it. The community
SHALL be visible on the chat's full info, and actors SHALL be able to trigger the
community service messages for a chat being added to, or removed from, a community.

#### Scenario: Community is visible on chat info

- **WHEN** a handler fetches full info for a chat attached to a community
- **THEN** the returned chat carries that community

#### Scenario: Chat added to a community

- **WHEN** the corresponding service message is triggered
- **THEN** the handler receives a message carrying the community, and the message is stored
  in the chat

#### Scenario: Chat removed from a community

- **WHEN** the removal service message is triggered
- **THEN** the handler receives it and the chat is no longer attached to the community

### Requirement: The whole edit surface mutates stored messages

Editing a stored message's media, live location or checklist SHALL mutate that message in
place rather than returning a synthesized result, and stopping a live location SHALL
return the stored message. Each SHALL fail with `TelegramBadRequest` when the target
message is unknown or deleted, matching the behavior of the already-modeled text and caption
edits, and SHALL fail with `WorldLookupError` when the target is an inline message, which the
toolkit does not model.

#### Scenario: Editing media replaces the stored media

- **WHEN** a handler calls `editMessageMedia` on a photo message it sent earlier
- **THEN** the stored message carries the new media in the field matching the input media
  type, its caption reflects the new input, and no additional message is added to the chat

#### Scenario: Editing a live location moves the stored message

- **WHEN** a handler calls `editMessageLiveLocation` on a message it sent with
  `sendLivePhoto` or `sendLocation`
- **THEN** the stored message's `location` reports the new coordinates

#### Scenario: Stopping a live location returns the stored message

- **WHEN** a handler calls `stopMessageLiveLocation` for a stored message
- **THEN** the returned `Message` is that stored message, not a synthesized one

#### Scenario: Editing an unknown message fails like Telegram

- **WHEN** a handler edits the media of a message that was deleted
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Editing an inline message says it is unmodeled

- **WHEN** a handler edits the media of a message addressed by `inline_message_id`
- **THEN** the call raises `WorldLookupError` naming inline messages as unmodeled, rather
  than silently succeeding or claiming Telegram refused it

### Requirement: A sent message carries the values its request stated

A message the environment stores SHALL carry the scalar values its request actually
carried, rather than synthesized substitutes, wherever the request states them. Media
content itself remains synthesized.

#### Scenario: A sent location keeps its coordinates

- **WHEN** a handler calls `sendLocation` with a latitude, longitude and live period
- **THEN** the stored message's `location` reports those values, not synthesized ones

#### Scenario: A request field is not forced into an incompatible payload field

- **WHEN** a request field shares a name with a payload field of a different type, such as
  a `sendVideo` cover file id against a `Video.cover` photo
- **THEN** the payload field keeps its synthesized value rather than the raw request value

### Requirement: Batch forward and copy produce real messages

Forwarding or copying several messages at once SHALL apply the same world semantics as the
single-message forms, appending one message per source to the target chat and returning
identifiers that exist in that chat.

#### Scenario: Forwarding a batch

- **WHEN** a handler calls `forwardMessages` with three message ids from another chat
- **THEN** three messages appear in the target chat carrying forward origin information,
  and the returned identifiers match their stored `message_id` values

#### Scenario: Copying a batch omits the source attribution

- **WHEN** a handler calls `copyMessages`
- **THEN** the copies appear in the target chat without forward origin information

#### Scenario: A batch from an unknown chat fails

- **WHEN** a handler forwards messages from a chat the environment does not know
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Unpinning all messages clears the pinned list

`unpinAllChatMessages` SHALL clear the chat's pinned message list that `pinChatMessage`
and `unpinChatMessage` maintain.

#### Scenario: Clearing every pin

- **WHEN** a handler pins two messages and then calls `unpinAllChatMessages`
- **THEN** the chat reports no pinned messages

### Requirement: Seeded results are drawn from the world

For methods with no state to mutate but an identifiable answer, the environment SHALL
answer from the world rather than from generic synthesis: `sendChatAction` SHALL verify
the chat exists, `getFile` SHALL echo the requested `file_id`, `createInvoiceLink` SHALL
return a deterministic link, and `getUserPersonalChatMessages` SHALL read from that user's
private chat when the environment knows one.

#### Scenario: A chat action against an unknown chat fails

- **WHEN** a handler calls `sendChatAction` for a chat that does not exist
- **THEN** the call raises `TelegramBadRequest`, and a call against a known chat returns
  `True` and is recorded

#### Scenario: getFile echoes the requested file

- **WHEN** a handler calls `getFile` with a `file_id` it obtained from a stored message
- **THEN** the returned `File` carries that same `file_id`

### Requirement: The bot's own profile is world state

The environment SHALL hold the bot's own configuration — commands, name, description,
short description, default administrator rights and menu buttons — as world state, keyed
by scope and language code where the Bot API keys them that way. A blueprint SHALL be able
to declare an initial profile, and every environment built from it SHALL start from an
independent copy.

#### Scenario: Declaring an initial profile

- **WHEN** a blueprint declares the bot's commands and a handler calls `getMyCommands`
- **THEN** the declared commands are returned without any setter having been called

#### Scenario: Profile state is isolated between environments

- **WHEN** two environments are built from one blueprint and one of them sets a new bot
  name
- **THEN** the other environment still reports the declared name

### Requirement: Bot profile setters and getters round-trip

The bot profile methods SHALL be applied to that state rather than synthesized:
`setMyCommands`, `deleteMyCommands`, `setMyName`, `setMyDescription`,
`setMyShortDescription`, `setMyDefaultAdministratorRights` and `setChatMenuButton` write,
and `getMyCommands`, `getMyName`, `getMyDescription`, `getMyShortDescription`,
`getMyDefaultAdministratorRights` and `getChatMenuButton` read back exactly what was
written for the same scope and language.

#### Scenario: Commands set for a scope are read back for that scope

- **WHEN** a handler sets two commands for the default scope and then calls
  `getMyCommands` for the default scope
- **THEN** those two commands are returned in order

#### Scenario: Commands are keyed by scope and language

- **WHEN** commands are set for the default scope in one language and read back for a
  different language
- **THEN** the environment returns an empty list, because the Bot API stores and returns
  each scope-and-language pair independently rather than falling back

#### Scenario: Deleting commands empties that key only

- **WHEN** commands are set for two scopes and `deleteMyCommands` is called for one of them
- **THEN** that scope reports an empty list and the other scope is unaffected

#### Scenario: A localized text falls back to the default language

- **WHEN** the bot's description is set with no language code and then read back for a
  language that has no dedicated description
- **THEN** the default-language description is returned, because the Bot API applies it to
  every user without a dedicated one

#### Scenario: Clearing a localized text restores the fallback

- **WHEN** a dedicated description is set for a language and then set to an empty string
- **THEN** reading that language returns the default-language description again

#### Scenario: Name, description and rights round-trip

- **WHEN** a handler sets the bot's name, description, short description and default
  administrator rights and then reads each back
- **THEN** each getter returns the value that was set

#### Scenario: A per-chat menu button overrides the default

- **WHEN** a handler sets a menu button for one private chat and leaves another unset
- **THEN** `getChatMenuButton` returns the per-chat button for the first chat and the
  default button for the second

### Requirement: Unset profile values return documented defaults

Reading a profile value that was never set SHALL return the value the Bot API documents
for that method rather than a synthesized object: an empty list for commands, an empty
string for description and short description, `MenuButtonDefault` for the menu button,
all-`False` administrator rights, and the bot's own first name for the bot name.

#### Scenario: An unconfigured bot reports documented defaults

- **WHEN** a handler reads commands, description, short description, menu button and
  default administrator rights from an environment whose profile was never configured
- **THEN** each returns its documented empty or default value, not synthesized content

### Requirement: Outstanding queries are tracked and answers validated

Every trigger that produces a query — callback query, inline query, shipping query,
pre-checkout query — SHALL register that query's identifier as outstanding. The
corresponding answer methods SHALL be applied to that registry: answering an outstanding
query SHALL succeed and clear it, and answering an unknown, expired or already-answered
identifier SHALL raise `TelegramBadRequest`. A pre-checkout query SHALL expire 10 seconds
after it was issued, by the world clock; other kinds do not expire.

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

### Requirement: Chat join requests are world state

A blueprint SHALL be able to declare pending join requests, and a trigger SHALL produce a
`chat_join_request` update while recording the request. `approveChatJoinRequest` SHALL make
the requester a member of the chat and clear the request; `declineChatJoinRequest` SHALL
clear the request without adding the member. Both SHALL raise `TelegramBadRequest` when no
such request is pending.

#### Scenario: Approving a request adds the member

- **WHEN** a user actor requests to join a chat and a handler approves it
- **THEN** the request is no longer pending and the user is a member of that chat

#### Scenario: Declining a request leaves the user out

- **WHEN** a handler declines a pending request
- **THEN** the request is no longer pending and the user is not a member

#### Scenario: Acting on a request that does not exist fails

- **WHEN** a handler approves a join request for a user who never requested to join
- **THEN** the call raises `TelegramBadRequest`

### Requirement: A payment flow can be driven end to end

The environment SHALL support exercising a full payment interaction: a shipping query, a
pre-checkout query, and the resulting message carrying `successful_payment`. Each step
SHALL be an actor trigger, and the bot's answers SHALL be validated against the query
registry.

#### Scenario: Completing a payment

- **WHEN** a test triggers a shipping query, the handler answers it, a pre-checkout query
  follows, the handler answers that, and the payment is triggered
- **THEN** a message carrying `successful_payment` is appended to the chat and reaches the
  handler registered for it

#### Scenario: Failing a pre-checkout

- **WHEN** a handler answers a pre-checkout query with `ok=False` and an error message
- **THEN** the call succeeds, the query is cleared, and no `successful_payment` message is
  produced unless the test triggers one

### Requirement: Channel chats are declarable

A blueprint SHALL be able to declare a channel chat, and messages posted to it SHALL route
as channel posts. Editing a stored channel post SHALL produce an `edited_channel_post`
update.

#### Scenario: Declaring a channel

- **WHEN** a blueprint declares a channel and a post is triggered in it
- **THEN** the handler registered for `channel_post` receives it, and the handler
  registered for `message` does not

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

### Requirement: Voting updates the stored poll

Voting SHALL be an actor trigger that produces a `poll_answer` update and records the
vote against the stored poll, updating its counts. Retracting a vote SHALL be supported
where Telegram supports it. An anonymous poll SHALL additionally be triggerable as a
`poll` update carrying aggregate state.

#### Scenario: A vote reaches the handler and the poll

- **WHEN** a user actor votes for the second option of a stored poll
- **THEN** a `poll_answer` update reaches the registered handler, and the stored poll
  reports one vote for that option

#### Scenario: Vote counts stay consistent with voters

- **WHEN** three users vote across two options and one of them retracts
- **THEN** each option's reported count equals the number of users recorded as having
  chosen it

#### Scenario: Voting in a closed poll fails

- **WHEN** a user actor votes in a poll that has been stopped
- **THEN** the trigger raises an error rather than recording the vote

### Requirement: Stopping a poll closes the stored poll

`stopPoll` SHALL close the poll stored on the target message and return it with its final
vote counts. Stopping a message that is unknown, carries no poll, or whose poll is already
closed SHALL raise `TelegramBadRequest`.

#### Scenario: Stopping returns the poll that was sent

- **WHEN** a handler sends a poll, users vote, and the handler stops it
- **THEN** the returned poll is the stored one, marked closed, carrying the votes cast

#### Scenario: Stopping twice fails

- **WHEN** a handler stops a poll that is already closed
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Stopping a message with no poll fails

- **WHEN** a handler calls `stopPoll` on an ordinary text message
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Reactions are world state

The environment SHALL record the reactions set on a message, per user, and expose them
through the chat rather than through the stored message — the Bot API has no message field
carrying them. `setMessageReaction` (the bot's own reactions on one message),
`deleteMessageReaction` (one actor's reaction off one message) and
`deleteAllMessageReactions` (one actor's reactions across the whole chat) SHALL each be
applied to that state with their own semantics rather than synthesized. The two
message-scoped methods SHALL fail with `TelegramBadRequest` for an unknown or deleted
message.

#### Scenario: The bot reacts to a message

- **WHEN** a handler calls `setMessageReaction` on a stored message
- **THEN** the chat reports that reaction as set by the bot for that message

#### Scenario: Reacting again replaces the previous reaction

- **WHEN** a handler sets a different reaction on a message it already reacted to
- **THEN** the chat reports only the new reaction for the bot

#### Scenario: Counts are aggregated across reactors

- **WHEN** two users and the bot react to the same message
- **THEN** the chat reports a count per distinct reaction matching the number of reactors

#### Scenario: Moderating one reaction off one message

- **WHEN** two users have reacted to a message and a handler calls
  `deleteMessageReaction` naming one of them
- **THEN** only that user's reaction is gone and the other user's remains

#### Scenario: Moderating one actor's reactions across the chat

- **WHEN** a user has reacted to several messages and a handler calls
  `deleteAllMessageReactions` naming that user
- **THEN** none of that user's reactions remain anywhere in the chat, while other users'
  reactions on the same messages are untouched — the method removes an actor's reactions
  chat-wide, not every reaction on one message

### Requirement: Reaction triggers derive from stored state

A user actor SHALL be able to react to a stored message, producing a `message_reaction`
update whose `old_reaction` and `new_reaction` are derived from that message's stored
reactions rather than fabricated, and a `message_reaction_count` update SHALL be
triggerable for the anonymous aggregate form.

#### Scenario: Changing a reaction reports the previous one

- **WHEN** a user actor reacts to a message and then reacts with a different emoji
- **THEN** the second `message_reaction` update reports the first emoji as
  `old_reaction` and the second as `new_reaction`

#### Scenario: Removing a reaction

- **WHEN** a user actor removes its reaction from a message
- **THEN** a `message_reaction` update with an empty `new_reaction` is dispatched and the
  chat no longer reports that user's reaction

### Requirement: Chat metadata is writable world state

The chat administration methods SHALL be applied to the world instead of being
synthesized: changing a chat's title, description and permissions, setting and deleting
its sticker set, and deleting its photo. The already-modeled `getChat` SHALL report the
mutated values.

#### Scenario: Renaming a chat is visible to getChat

- **WHEN** a handler calls `setChatTitle` on a group and then calls `getChat`
- **THEN** the returned chat carries the new title

#### Scenario: Description and permissions round-trip

- **WHEN** a handler sets a chat description and chat permissions
- **THEN** `getChat` reports both, and neither affects any other chat in the environment

#### Scenario: Deleting a chat photo clears it

- **WHEN** a chat declared with a photo has `deleteChatPhoto` called on it
- **THEN** `getChat` reports no photo

#### Scenario: Administering an unknown chat fails

- **WHEN** a handler sets the title of a chat the environment does not know
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Administering a private chat fails

- **WHEN** a handler calls `setChatTitle` on a private chat
- **THEN** the call raises `TelegramBadRequest`, as Telegram does

### Requirement: Chat administration emits service messages

Where Telegram posts a service message for an administrative action, the environment SHALL
append the matching message to the chat so handlers filtering on it can be exercised.

#### Scenario: A title change posts a service message

- **WHEN** a handler calls `setChatTitle`
- **THEN** a message carrying `new_chat_title` with the new title is appended to the chat

#### Scenario: A photo deletion posts a service message

- **WHEN** a handler calls `deleteChatPhoto`
- **THEN** a message carrying `delete_chat_photo` is appended to the chat

### Requirement: Membership reads are derived from membership state

`getChatAdministrators` and `getChatMemberCount` SHALL be answered from the chat's stored
members, which the already-modeled ban, unban, promote and restrict methods maintain,
rather than being synthesized.

#### Scenario: Promoting a user changes the administrator list

- **WHEN** a handler promotes a member and then calls `getChatAdministrators`
- **THEN** the returned list contains that user with an administrator status, alongside
  the chat's creator

#### Scenario: Other bots are omitted unless asked for

- **WHEN** another bot is an administrator and `getChatAdministrators` is called without
  `return_bots`
- **THEN** that bot is absent from the result, and passing `return_bots` includes it

#### Scenario: Member count follows membership changes

- **WHEN** a handler bans a member of a chat with three members and then calls
  `getChatMemberCount`
- **THEN** the returned count reflects the removal

#### Scenario: Reading members of an unknown chat fails

- **WHEN** a handler calls `getChatMemberCount` for a chat the environment does not know
- **THEN** the call raises `TelegramBadRequest`

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

### Requirement: The bot's own standing in a chat is declarable

A blueprint SHALL be able to declare what status the bot itself holds in a group, supergroup
or channel, either through a `bot_status` argument of the `add_*` helper or by naming
`blueprint.bot` in that chat's `members`. Declaring it both ways SHALL be rejected rather than
resolved, so neither spelling can silently shadow the other. Absent any declaration the bot
SHALL be an ordinary member of every such chat.

#### Scenario: Declaring the bot as an administrator

- **WHEN** a blueprint declares a supergroup with `bot_status` set to administrator and a
  handler calls `getChatMember` for the bot's own id
- **THEN** the administrator status is reported, so a handler gating itself on its own
  standing takes the same branch it would in production

#### Scenario: The two spellings are equivalent

- **WHEN** the bot's status is declared through `members` instead
- **THEN** the same status is reported

#### Scenario: Declaring it twice is rejected

- **WHEN** a blueprint passes both `bot_status` and an explicit `members` entry for the bot
- **THEN** the declaration raises, including when the status passed is the default one

### Requirement: Membership rights and permissions are declared state

A member's administrator rights and a restricted member's permissions SHALL be part of the
declared and stored membership, not invented when the membership is read. A blueprint SHALL be
able to declare them for any member, the bot included, through `Blueprint.set_member`; an
administrator declared without rights SHALL hold the ordinary administrator rights, and a
restriction declared without permissions SHALL deny everything. `administrator_rights(...)`
SHALL build the ordinary administrator rights with named overrides, so the case a test cares
about — an administrator lacking one right — is a single declaration.

#### Scenario: The bot is declared to lack a right

- **WHEN** a blueprint declares the bot as an administrator whose rights deny message
  deletion, and a handler reads its own membership
- **THEN** that right is reported as denied and the others as granted

#### Scenario: An administrator declared without rights has the ordinary ones

- **WHEN** a member is declared with the administrator status and nothing else
- **THEN** reading the membership reports the ordinary administrator rights

#### Scenario: A restricted member can be declared

- **WHEN** a member is declared with permissions
- **THEN** the membership is reported as restricted, carrying those permissions

#### Scenario: Rights and permissions belong to different statuses

- **WHEN** a declaration names both rights and permissions for one member
- **THEN** it is rejected, because no single membership carries both

#### Scenario: Declared rights reach the administrator list

- **WHEN** `getChatAdministrators` is called for a chat with a declared administrator
- **THEN** the entry for that administrator carries the declared rights

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

### Requirement: Rights are reported per chat type

A membership read SHALL report each administrator right the way the Bot API reports it for
that chat's type: a right the API does not report there SHALL come back unset however it was
declared or granted, and a right it does report SHALL come back as a plain boolean even when
it was never stated.

#### Scenario: A supergroup administrator

- **WHEN** a handler reads an administrator's membership in a supergroup
- **THEN** the channel-only rights are unset while the supergroup rights carry booleans

#### Scenario: A channel administrator

- **WHEN** a handler reads an administrator's membership in a channel
- **THEN** the channel rights carry booleans while the supergroup-only rights are unset

#### Scenario: Granting a right where it cannot exist

- **WHEN** a handler promotes a member granting a right the chat's type does not report
- **THEN** reading the member back reports that right as unset rather than granted

### Requirement: The chat owner cannot be demoted, banned or restricted

Promoting, demoting, banning or restricting the chat's creator SHALL fail with the error
Telegram answers all four with, so a bot that moderates a list of users fails in the test
rather than only in production.

#### Scenario: Acting on the owner fails

- **WHEN** a handler bans, restricts, promotes or demotes the chat's creator
- **THEN** the call raises `TelegramBadRequest` reporting that the chat owner cannot be removed

#### Scenario: Banning first is not a way around the guard

- **WHEN** a handler bans the owner and then promotes them
- **THEN** the first call already fails, so the owner's standing is never lost

### Requirement: Invite links are chat state

The environment SHALL store a chat's invite links, each carrying its URL, creator, name,
expiry, member limit, join-request flag, subscription period and price where applicable,
and whether it has been revoked. A blueprint SHALL be able to declare existing links, and
every environment built from it SHALL start from an independent copy.

#### Scenario: Declaring an existing link

- **WHEN** a blueprint declares an invite link on a chat and a handler edits it
- **THEN** the edit applies to the declared link without it having been created first

#### Scenario: Links are isolated between environments

- **WHEN** two environments are built from one blueprint and one of them revokes a
  declared link
- **THEN** the other environment still reports that link as active

### Requirement: Invite link methods act on stored links

`createChatInviteLink`, `createChatSubscriptionInviteLink`, `editChatInviteLink`,
`editChatSubscriptionInviteLink` and `revokeChatInviteLink` SHALL be applied to the chat's
stored links. Editing and revoking SHALL return the stored link, mutated — never a newly
synthesized object — so a link created earlier can be correlated with a later operation.

#### Scenario: Creating then revoking returns the same link

- **WHEN** a handler creates an invite link, stores its URL, and later revokes that URL
- **THEN** the revoked link returned is the one that was created, now marked revoked

#### Scenario: Editing mutates the stored link

- **WHEN** a handler edits an invite link's name and member limit
- **THEN** the returned link carries the new name and limit, and reading the chat's links
  shows the same values

#### Scenario: A subscription link keeps its subscription fields

- **WHEN** a handler creates a subscription invite link and then edits its name
- **THEN** the returned link keeps its subscription period and price, and carries the new
  name

#### Scenario: Acting on an unknown link fails

- **WHEN** a handler edits or revokes an invite link URL the chat does not have
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: An unsupported subscription period fails

- **WHEN** a handler creates a subscription invite link with a subscription period other
  than the value the Bot API permits
- **THEN** the call raises `TelegramBadRequest`

### Requirement: The primary invite link is reported by getChat

`exportChatInviteLink` SHALL replace the chat's primary invite link, revoking the previous
one and returning the new URL, and revoking the primary link SHALL generate a replacement
as Telegram does. The already-modeled `getChat` SHALL report the current primary link.

#### Scenario: Exporting replaces the primary link

- **WHEN** a handler calls `exportChatInviteLink` twice
- **THEN** the two returned URLs differ, the first is marked revoked, and `getChat`
  reports the second

#### Scenario: getChat reports the primary link

- **WHEN** a handler exports an invite link and then calls `getChat`
- **THEN** the chat's `invite_link` is the exported URL

#### Scenario: Revoking the primary link generates a replacement

- **WHEN** a handler revokes the chat's current primary link
- **THEN** the revoked link is returned marked revoked, and `getChat` reports a different,
  active primary link

### Requirement: The record-only surface is an enumerated decision

The toolkit SHALL name the Bot API surfaces it does not model and does not intend to,
together with the reason each is excluded: nothing a test reads back, media processing, or
a layer the toolkit deliberately does not drive. Clusters whose modeling is deferred rather
than refused SHALL be listed separately, so "not yet" is distinguishable from "no".

#### Scenario: A contributor can tell refusal from deferral

- **WHEN** someone asks whether a given unmodeled method should be modeled
- **THEN** the answer is readable from the enumerated lists rather than inferred from the
  absence of an implementation

#### Scenario: The documentation shows the same boundary

- **WHEN** a user looks for a method in the documentation
- **THEN** they can see whether it is modeled, deliberately record-only, or a deferred
  candidate

### Requirement: File content is declarable world state

The environment SHALL be able to hold the content of a file by its identifier, declared on
a blueprint, and SHALL serve that content to the framework's download helpers. `getFile`
SHALL report a size consistent with the content the environment holds.

#### Scenario: A declared file downloads its content

- **WHEN** a blueprint declares content for a file identifier and a handler downloads that
  file
- **THEN** the downloaded bytes are the declared content

#### Scenario: File size matches the content

- **WHEN** a handler calls `getFile` for an identifier the environment holds content for
- **THEN** the returned `File` reports the size of that content

#### Scenario: Declared content is isolated between environments

- **WHEN** two environments are built from one blueprint
- **THEN** content registered during one test is not visible to the other

### Requirement: Uploaded content is readable back

When a handler sends a file whose input carries its bytes directly, the environment SHALL
store those bytes against the resulting message's file identifier, so a bot that uploads
and then downloads within one test reads back what it sent.

#### Scenario: Round-tripping an uploaded document

- **WHEN** a handler sends a document built from an in-memory buffer and then downloads the
  file identifier from the stored message
- **THEN** the downloaded bytes are the bytes that were sent

### Requirement: Downloading content the environment does not have fails loudly

Downloading a file the environment holds no content for SHALL raise an error naming the
file and the ways to proceed, rather than yielding empty content. A testing tool must not
answer a question it cannot answer with a value that looks like an answer.

#### Scenario: An undeclared download raises

- **WHEN** a handler downloads a file whose content was never declared or uploaded
- **THEN** the call raises an error naming the file identifier and mentioning both
  declaring content and overriding the call

#### Scenario: The error is not silently swallowed by the download helpers

- **WHEN** the failure occurs inside `bot.download` or `bot.download_file`
- **THEN** the error surfaces to the test rather than leaving an empty destination

### Requirement: The bot's star balance is a ledger

The environment SHALL record every movement of Telegram Stars as a transaction, and SHALL
derive the bot's balance from those transactions rather than storing it separately. A
blueprint SHALL be able to declare a starting balance. `getMyStarBalance` and
`getStarTransactions` SHALL read that ledger.

#### Scenario: A payment credits the balance

- **WHEN** a user actor completes a payment in stars
- **THEN** the bot's balance increases by the amount paid, and the transaction appears in
  `getStarTransactions`

#### Scenario: The balance always matches the transactions

- **WHEN** any sequence of payments, refunds and gift purchases has been applied
- **THEN** the reported balance equals the sum of the recorded transactions plus the
  declared starting balance

#### Scenario: A declared balance needs no payment first

- **WHEN** a blueprint declares a starting balance and a handler reads it
- **THEN** the declared amount is returned without any payment having been triggered

### Requirement: Refunds resolve a real charge

`refundStarPayment` SHALL resolve the `telegram_payment_charge_id` of a payment the
environment recorded, debit the bot's balance, and mark the charge refunded. Refunding a
charge already refunded SHALL raise `TelegramBadRequest`; refunding a charge the environment
never recorded SHALL raise `WorldLookupError`, since there is no payment for the test to have
refunded.

#### Scenario: Refunding a payment the bot received

- **WHEN** a user actor pays and the handler refunds the charge id from the resulting
  message
- **THEN** the refund succeeds and the bot's balance returns to what it was before the
  payment

#### Scenario: Refunding twice fails

- **WHEN** a handler refunds the same charge a second time
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Refunding a charge that never existed fails

- **WHEN** a handler refunds a fabricated charge id
- **THEN** the call raises `WorldLookupError`

### Requirement: Star subscriptions can be cancelled and re-enabled

`editUserStarSubscription` SHALL act on the subscription behind a recorded charge, and the
environment SHALL reflect whether that subscription is cancelled.

#### Scenario: Cancelling a subscription

- **WHEN** a handler cancels the subscription behind a charge it received
- **THEN** the environment reports that subscription as cancelled, and re-enabling it
  reverses that

#### Scenario: Acting on an unknown subscription fails

- **WHEN** a handler cancels a subscription for a charge the environment does not know
- **THEN** the call raises `WorldLookupError`

### Requirement: Gifts are owned inventory

`sendGift` SHALL create an owned gift for its recipient and spend its cost from the bot's
balance. `getUserGifts`, `getChatGifts` and `getBusinessAccountGifts` SHALL read that
inventory, and `convertGiftToStars`, `upgradeGift` and `transferGift` SHALL move it.
`getAvailableGifts` SHALL return a stable catalogue.

#### Scenario: Sending a gift creates owned inventory

- **WHEN** a handler sends a gift to a user
- **THEN** that gift appears in the user's owned gifts, and the bot's balance falls by its
  cost

#### Scenario: The catalogue is stable

- **WHEN** a handler calls `getAvailableGifts` twice
- **THEN** the same gifts are returned in the same order, so a test can pick one
  deterministically

#### Scenario: Converting a gift returns its stars

- **WHEN** a handler converts an owned gift to stars
- **THEN** the gift leaves the inventory and the balance rises

#### Scenario: Transferring moves ownership

- **WHEN** a handler transfers an owned unique gift to another chat
- **THEN** the gift appears in the new owner's inventory and leaves the previous owner's

#### Scenario: Acting on a gift that is not owned fails

- **WHEN** a handler converts, upgrades or transfers an `owned_gift_id` the environment
  does not know
- **THEN** the call raises `WorldLookupError`

#### Scenario: A gift id outside the catalogue says what the catalogue holds

- **WHEN** a handler sends a gift whose id is not one the fake offers
- **THEN** the call raises `WorldLookupError` listing the available ids and naming the
  override to use for a real one

### Requirement: Star rights are not enforced

The environment SHALL NOT enforce the business bot rights the Bot API requires for gift and
star operations, consistent with the toolkit not enforcing rights anywhere.

#### Scenario: A gift operation without the right still succeeds

- **WHEN** a handler converts a gift on a connection whose rights do not permit it
- **THEN** the call succeeds, and a test needing the rejection declares it with an override

### Requirement: Sticker sets are world state

The environment SHALL hold sticker sets by name, each carrying its title, sticker type and
the stickers it contains. A blueprint SHALL be able to declare existing sets, and every
environment built from it SHALL start from an independent copy.

#### Scenario: A declared set is readable

- **WHEN** a blueprint declares a sticker set and a handler calls `getStickerSet`
- **THEN** the declared set is returned without it having been created through the API

#### Scenario: Sets are isolated between environments

- **WHEN** two environments are built from one blueprint and one of them adds a sticker
- **THEN** the other still reports the declared contents

### Requirement: The sticker set lifecycle is modeled

Creating a set, adding, deleting and replacing its stickers, renaming it and deleting it
SHALL be applied to that registry, and `getStickerSet` SHALL report the result. A name
already taken, and replacing a sticker the named set does not contain, SHALL fail with
`TelegramBadRequest`, as Telegram does. Naming a set that does not exist, or a sticker that is
in no set at all, SHALL fail with `WorldLookupError`: the environment holds only the sets the
test declared or created, so that is a gap in the setup rather than a Telegram rejection.

#### Scenario: Create then add then read back

- **WHEN** a handler creates a set, adds a sticker to it, and calls `getStickerSet`
- **THEN** the returned set carries both the original and the added sticker

#### Scenario: A bot can check a set before writing to it

- **WHEN** a handler reads a set to decide whether it is full, then adds a sticker
- **THEN** the count it read reflects the stickers actually in the set

#### Scenario: Creating a set whose name is taken fails

- **WHEN** a handler creates a set with a name that already exists
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Reading or writing an unknown set fails

- **WHEN** a handler reads, renames, deletes or adds to a set that does not exist
- **THEN** the call raises `WorldLookupError`

#### Scenario: Removing a sticker that is not in the set fails

- **WHEN** a handler replaces a sticker the named set does not contain
- **THEN** the call raises `TelegramBadRequest`, while deleting a sticker that is in no set at
  all raises `WorldLookupError`, since no set is named to reject it

#### Scenario: Deleting a set removes it

- **WHEN** a handler deletes a set and then reads it
- **THEN** the read raises `WorldLookupError`

### Requirement: Sticker files are seeded, not modeled

`uploadStickerFile` SHALL return a stable file identifier the set methods can then
reference, and `getCustomEmojiStickers` SHALL echo the identifiers it was asked for. Neither
SHALL imply that sticker image data exists.

#### Scenario: An uploaded file can be added to a set

- **WHEN** a handler uploads a sticker file and adds the returned identifier to a set
- **THEN** the set reports a sticker carrying that identifier

#### Scenario: Custom emoji lookups echo their input

- **WHEN** a handler requests custom emoji stickers by identifier
- **THEN** one sticker is returned per requested identifier, carrying it

### Requirement: Per-sticker attributes stay record-only

Setting a sticker's emoji list, keywords, mask position or position in a set, and setting
either kind of set thumbnail, SHALL remain recorded and synthesized rather than modeled:
nothing reads them back, and thumbnails are media processing.

#### Scenario: An attribute setter is recorded but changes nothing

- **WHEN** a handler sets a sticker's keywords
- **THEN** the call succeeds and is visible in the call log, and the stored set is unchanged

### Requirement: A rich message carries the content its request stated

A rich message the environment stores, whether sent, edited, copied or forwarded, SHALL
carry the blocks and settings its request stated, in the shape Telegram returns them. Media
inside a block SHALL be synthesized as it is for the matching send method. A field the
stored shape requires but the request left unset SHALL get a valid value. Content given
only as `html` or `markdown` is not parsed into blocks.

#### Scenario: Sent blocks are stored

- **WHEN** a handler sends a rich message whose blocks include a paragraph, a list, a table
  and a button block
- **THEN** the stored message's rich content has the same blocks in the same order,
  carrying the same text, cells and buttons

#### Scenario: Media inside a block is synthesized

- **WHEN** a handler sends a rich message containing a photo block marked as a spoiler
- **THEN** the stored block carries a non-empty, schema-valid photo, the same as a photo
  sent with `sendPhoto`, and is marked as a spoiler

#### Scenario: Unset required fields get valid values

- **WHEN** a handler sends a map block without zoom or size, or a list without item labels
- **THEN** the stored blocks carry values within the ranges the Bot API documents for them

#### Scenario: Markup-only content is not parsed

- **WHEN** a handler sends a rich message given only as `html` or `markdown`
- **THEN** the message is stored and returned, and its rich content carries no blocks

#### Scenario: A copied rich message keeps its content

- **WHEN** a handler copies or forwards a stored rich message
- **THEN** the resulting message carries the same rich content

### Requirement: Editing text replaces either kind of content

`editMessageText` SHALL replace a stored message's content with what the request carries:
rich content replaces text and text replaces rich content, so the message never carries
both. The reply markup SHALL follow the method's existing rule: what the request passes,
and none when it passes none.

#### Scenario: Editing in rich content

- **WHEN** a handler edits a stored text message with rich content
- **THEN** the stored message carries the new blocks and no longer carries the old text

#### Scenario: Editing a rich message back to text

- **WHEN** a handler edits a stored rich message with plain text
- **THEN** the stored message carries the text and no longer carries rich content

#### Scenario: Editing only the keyboard keeps the rich content

- **WHEN** a handler edits the reply markup of a stored rich message
- **THEN** the rich content is unchanged and the new keyboard is stored

### Requirement: Buttons inside rich content are clickable

A click trigger SHALL resolve a `callback_data` from a button anywhere in a stored rich
message's content, at any nesting depth, as well as from its inline keyboard, and SHALL
accept such a button object directly. Buttons SHALL be considered in document order: the
inline keyboard first, then the blocks. Deep-link following and the misdirected-click hint
SHALL cover these buttons the same way.

#### Scenario: Clicking a button block

- **WHEN** a handler sends a rich message with a callback button in a button block, and a
  user actor clicks its `callback_data`
- **THEN** a `callback_query` update is dispatched whose `data` is that `callback_data` and
  whose `message` is the stored rich message

#### Scenario: Clicking a button nested in text

- **WHEN** the callback button sits in rich text inside a nested block, such as a list item
  or a details block
- **THEN** the click resolves it exactly as it resolves a top-level button block

#### Scenario: Clicking a rich button object

- **WHEN** a test passes a button object taken from stored rich content to the click
  trigger
- **THEN** the click uses that button's `callback_data`

#### Scenario: Following a deep link from a rich button

- **WHEN** a handler sends a rich message whose `url` button carries a start link to the
  bot, and a user actor follows the deep link
- **THEN** the link is followed exactly as it is from an inline keyboard button

#### Scenario: A rich button in another chat is named

- **WHEN** an actor clicks a `callback_data` that exists only on a rich button in a
  different chat
- **THEN** the failure names that chat, as it does for an inline keyboard button

### Requirement: A restriction is reported separately from presence

A restricted user SHALL be reported with `is_member` telling whether they are in the chat,
and SHALL count as a member only while they are. Restricting a user who is not in the chat
SHALL leave them absent. A restricted member who leaves or rejoins SHALL stay restricted,
with only `is_member` changing, in both membership reads and membership updates.

#### Scenario: Restricting an absent user

- **WHEN** a handler restricts a user who never joined the chat
- **THEN** `getChatMember` reports them restricted with `is_member` false, and
  `getChatMemberCount` does not count them

#### Scenario: A restricted member leaves

- **WHEN** a restricted member's actor leaves the chat
- **THEN** the `chat_member` update moves them from restricted with `is_member` true to
  restricted with `is_member` false, and the permissions are unchanged

#### Scenario: A restricted user rejoins

- **WHEN** that user's actor joins again
- **THEN** they are restricted with `is_member` true and the same permissions

### Requirement: Granting every permission lifts a restriction

`restrictChatMember` granting every permission SHALL lift the restriction. The user SHALL
become a member if present and left otherwise, with no stored permissions or end date.

#### Scenario: Lifting a present member's restriction

- **WHEN** a handler restricts a member and then restricts them again granting every
  permission
- **THEN** `getChatMember` reports a plain member

#### Scenario: Lifting an absent user's restriction

- **WHEN** a handler lifts the restriction of a user who is not in the chat
- **THEN** `getChatMember` reports them as having left

### Requirement: Restriction and ban end dates are reported as Telegram reports them

A restriction or ban with no end SHALL report `until_date` as the Unix epoch, which is `0`
on the wire. A change to any status other than restricted or banned SHALL clear the stored
end date. A ban in a basic group SHALL have no end, since the Bot API applies `until_date`
for supergroups and channels only.

#### Scenario: A permanent ban

- **WHEN** a handler bans a user without an end date
- **THEN** `getChatMember` reports `until_date` as the Unix epoch

#### Scenario: Unbanning clears the end date

- **WHEN** a handler bans a user until a date and then unbans them
- **THEN** the user reads as having left, with no restriction end carried into a later
  membership

#### Scenario: A basic-group ban has no end

- **WHEN** a handler bans a user in a basic group with an end date
- **THEN** `getChatMember` reports `until_date` as the Unix epoch

### Requirement: The demote trigger demotes administrators only

The actor's demote trigger SHALL refuse, as a setup error, a subject who is not an
administrator, and SHALL leave their membership unchanged. Demoting is not a way to lift a
restriction or bring an absent user in.

#### Scenario: Demoting a restricted member is refused

- **WHEN** a test demotes a restricted member through the actor
- **THEN** the trigger fails as a setup error, and the member stays restricted

### Requirement: Unbanning honours `only_if_banned`

`unbanChatMember` SHALL leave the user absent and free to join, removing a present member as
the Bot API documents for the default. With `only_if_banned`, it SHALL act on a banned user
only and leave anyone else as they are.

#### Scenario: Unbanning removes a present member by default

- **WHEN** a handler unbans a user who is a member of the chat
- **THEN** the user reads as having left

#### Scenario: `only_if_banned` leaves a member alone

- **WHEN** a handler unbans a member of the chat with `only_if_banned`
- **THEN** the user is still a member

### Requirement: Ephemeral messages are addressed to one receiver

A message the bot sends with ephemeral message parameters SHALL be returned in Telegram's
ephemeral shape: message id 0, an ephemeral message id, and the receiver. It SHALL be kept
apart from the chat's shared history, readable back per receiver in send order, and SHALL
keep its topic thread. It SHALL be refused outside a group or supergroup, and for a
receiver the world does not declare.

#### Scenario: An ephemeral send has Telegram's shape

- **WHEN** a handler sends a message to a group with ephemeral message parameters naming a
  user
- **THEN** the returned message has `message_id` 0, an `ephemeral_message_id`, and that
  user as `receiver_user`

#### Scenario: The deprecated receiver parameter sends one too

- **WHEN** a handler sends a message to a group with the deprecated `receiver_user_id`
  parameter instead of ephemeral message parameters
- **THEN** the message is ephemeral for that user, exactly as with the new parameters

#### Scenario: An ephemeral message stays out of the shared history

- **WHEN** a handler sends an ephemeral message to a group
- **THEN** the group's message list does not contain it, and a wait for the next message in
  that group is not satisfied by it

#### Scenario: An ephemeral message is readable back for its receiver

- **WHEN** a test asks the chat for the ephemeral messages sent to a user
- **THEN** it gets the ephemeral messages the bot sent to that user, in the order they were
  sent, and none the user sent

#### Scenario: An ephemeral send outside a group is rejected

- **WHEN** a handler sends an ephemeral message to a private chat or a channel
- **THEN** the call fails as a Telegram error, and nothing is stored

#### Scenario: An ephemeral send to an undeclared user is a setup error

- **WHEN** a handler sends an ephemeral message naming a user the world does not declare
- **THEN** the call fails as a setup error naming that user, and nothing is stored

#### Scenario: An ephemeral send keeps its topic

- **WHEN** a handler sends an ephemeral message into a forum topic
- **THEN** the returned message carries that topic's thread identifier

### Requirement: Only the receiver can click an ephemeral message

A click trigger SHALL resolve buttons on the ephemeral messages addressed to the clicking
actor, ahead of the shared history, and on no other ephemeral message, including one passed
explicitly. A miss SHALL name the receiver of the ephemeral message that holds the button.
The produced `callback_query` SHALL carry the ephemeral message.

#### Scenario: The receiver clicks an ephemeral button

- **WHEN** a handler sends an ephemeral message with a callback button to a member, and
  that member's actor clicks it
- **THEN** a `callback_query` update is dispatched whose `message` is the ephemeral message,
  carrying its `ephemeral_message_id` and `receiver_user`

#### Scenario: Another member cannot click it

- **WHEN** a different member of the same chat clicks that `callback_data`, by data or by
  passing the ephemeral message itself
- **THEN** the click fails, and the failure names the member the ephemeral message is
  addressed to rather than reading as a `callback_data` that exists nowhere

#### Scenario: An answer cannot replace an ephemeral message

- **WHEN** a handler answers a callback query from an ephemeral message with an ephemeral
  message that asks to replace the original
- **THEN** the call fails as a Telegram error, because the Bot API requires ephemeral
  messages to be edited with the ephemeral edit methods instead

### Requirement: Ephemeral edits and deletions act on stored ephemeral messages

The ephemeral edit methods SHALL change the stored ephemeral message they name, addressed by
chat, receiver and ephemeral id: text or rich content, caption, media and reply markup. The
ephemeral delete method SHALL remove it. A call naming a message that does not exist for
that chat and receiver SHALL fail as a Telegram error. The regular edit and delete methods
SHALL NOT reach ephemeral messages.

#### Scenario: Editing an ephemeral message's text

- **WHEN** a handler edits the text of an ephemeral message it sent
- **THEN** the stored ephemeral message carries the new text, and the shared history is
  unchanged

#### Scenario: Deleting an ephemeral message

- **WHEN** a handler deletes an ephemeral message it sent
- **THEN** it is no longer readable back for its receiver, and a later edit of it fails

#### Scenario: Editing through the message's own shortcut

- **WHEN** a handler edits or deletes an ephemeral message through that message object's own
  ephemeral shortcuts
- **THEN** the calls address the stored message and succeed

#### Scenario: The wrong receiver does not match

- **WHEN** a handler edits an ephemeral message by its id but names a different receiver
- **THEN** the call fails as a Telegram error, and the stored message is unchanged

#### Scenario: Regular edits do not reach ephemeral messages

- **WHEN** a handler calls the regular text edit or delete shortcut on an ephemeral message
- **THEN** the call fails as a Telegram error, and the stored ephemeral message is unchanged

### Requirement: Actors can send ephemeral commands

The send trigger SHALL be able to produce an incoming ephemeral message, in a group or
supergroup only: message id 0 and an ephemeral message id, kept out of the shared history,
whether the actor produced it or a test fed it directly. A bot message replying to it SHALL
have to be ephemeral and SHALL have to name an incoming ephemeral message that exists in
that chat. Such a reply carries no `reply_to_message`.

#### Scenario: Sending an ephemeral command

- **WHEN** a user actor in a group sends a command marked as ephemeral, twice
- **THEN** each dispatched message has `message_id` 0 and its own `ephemeral_message_id`,
  and the group's message list contains neither

#### Scenario: Replying with the message's own reply shortcut

- **WHEN** a handler answers that command with `message.reply(...)`
- **THEN** the reply is an ephemeral message addressed to the command's sender, with no
  `reply_to_message`

#### Scenario: A non-ephemeral reply to an ephemeral message is rejected

- **WHEN** a handler replies to an ephemeral command by its `ephemeral_message_id` without
  ephemeral message parameters
- **THEN** the call fails as a Telegram error, and nothing is stored

#### Scenario: A reply must name an incoming ephemeral message

- **WHEN** a handler replies naming an `ephemeral_message_id` that no user sent in that
  chat, including the id of the bot's own ephemeral message
- **THEN** the call fails as a Telegram error, and nothing is stored

#### Scenario: An ephemeral command outside a group is a setup error

- **WHEN** a test sends an ephemeral command from an actor bound to a private chat
- **THEN** the trigger fails as a setup error, and nothing is dispatched

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

### Requirement: A media group stores its items

`sendMediaGroup` SHALL store one message per item, each carrying that item's media, caption
and caption entities, all under one shared `media_group_id`. A request with fewer than 2 or
more than 10 items SHALL fail as a Telegram error.

#### Scenario: An album keeps each item's media and caption

- **WHEN** a handler sends a media group of two photos with captions
- **THEN** two messages are stored, each with a photo and its own caption, sharing one
  `media_group_id`

#### Scenario: A one-item album is refused

- **WHEN** a handler sends a media group with one item
- **THEN** the call raises `TelegramBadRequest`, and nothing is stored

### Requirement: A reply resolves its target where the request says

A send with reply parameters SHALL look its target up in the chat the parameters name, or in
the target chat otherwise. It SHALL set `reply_to_message` only for a target in the same
chat, and SHALL describe a target in another chat with `external_reply`. A target that does not exist SHALL fail as a Telegram error, unless the request allows
sending without the reply.

#### Scenario: A reply to a missing message fails

- **WHEN** a handler replies to a message id that does not exist in the chat
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Sending without the reply is allowed when asked

- **WHEN** the same reply passes `allow_sending_without_reply`
- **THEN** the message is sent without `reply_to_message`

#### Scenario: A reply in another chat is looked up there

- **WHEN** a handler replies to a message of another chat, naming that chat
- **THEN** the target is resolved in that chat, and the message carries no
  `reply_to_message` from its own chat, but an `external_reply` naming the target's origin

### Requirement: Copies and forwards follow the documented rules

A copy or forward SHALL land in the target thread the request names, or in none. A copy
SHALL carry the request's new caption with its entities, drop the caption when asked, and
store the request's inline keyboard. Service, invoice, paid-media and giveaway messages SHALL
not be copied, and protected or service messages SHALL not be forwarded; a single call fails
as a Telegram error and a batch call skips them.

#### Scenario: A copy into a topic lands in it

- **WHEN** a handler copies a message into a forum topic of another chat
- **THEN** the copy carries that topic's thread, and a copy into a non-forum chat carries
  none

#### Scenario: A new caption brings its own entities

- **WHEN** a handler copies a captioned message with a new caption and no entities
- **THEN** the copy carries the new caption and none of the old entities

#### Scenario: A protected message cannot be forwarded

- **WHEN** a handler forwards a message sent with protected content
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: A service message cannot be copied

- **WHEN** a handler copies a service message
- **THEN** the call raises `TelegramBadRequest`, and a batch copy including it skips it

### Requirement: Unpinning without an id unpins the newest pin

`unpinChatMessage` without a message id SHALL unpin only the most recently sent pinned
message, leaving the others pinned.

#### Scenario: Two pins, one unpin

- **WHEN** a handler pins two messages and then unpins without an id
- **THEN** only the more recently sent message is unpinned

### Requirement: An edit acts on the content the message has

`editMessageText` SHALL fail as a Telegram error on a message with no text or rich content,
and `editMessageCaption` SHALL fail on a message with no media that can carry a caption.

#### Scenario: Editing text on a photo fails

- **WHEN** a handler edits the text of a photo message
- **THEN** the call raises `TelegramBadRequest`, and the stored message is unchanged

#### Scenario: Editing a caption on a text message fails

- **WHEN** a handler edits the caption of a text message
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Polls keep their documented settings

A poll SHALL store all of its correct option ids, and SHALL allow revoting by default unless
it is a quiz. A quiz without correct option ids SHALL fail as a Telegram error. `stopPoll`
SHALL store the inline keyboard it is given.

#### Scenario: A quiz keeps its correct answers

- **WHEN** a handler sends a quiz with two correct option ids
- **THEN** the stored poll reports both

#### Scenario: A regular poll allows revoting by default

- **WHEN** a handler sends a regular poll without saying whether revoting is allowed
- **THEN** the stored poll allows revoting

#### Scenario: A quiz without an answer is refused

- **WHEN** a handler sends a quiz with no correct option ids
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Forum topic calls apply their documented couplings

Hiding the General topic SHALL also close it, and reopening it SHALL also unhide it.
`editForumTopic` with an empty name SHALL keep the current name, and an empty custom emoji id
SHALL remove the icon.

#### Scenario: Hiding General closes it

- **WHEN** a handler hides an open General topic
- **THEN** the General topic is hidden and closed

#### Scenario: An empty name keeps the name

- **WHEN** a handler edits a topic with an empty name
- **THEN** the topic keeps its name

### Requirement: Business deletions stay in one chat

`deleteBusinessMessages` SHALL delete messages from one chat only, and SHALL fail as a
Telegram error when the ids belong to different chats. Business messages SHALL be numbered
per business connection, so two chats of one connection never hold the same id.

#### Scenario: Another chat's message is untouched

- **WHEN** two chats of a business connection each hold a business message, and a handler
  deletes the first one
- **THEN** the other chat's message stays

#### Scenario: Ids from two chats are refused

- **WHEN** a handler deletes business messages from two chats in one call
- **THEN** the call fails as a Telegram error, and nothing is deleted

### Requirement: Checklists carry their content

A checklist sent or edited SHALL be stored with the title and tasks its request stated.

#### Scenario: A sent checklist keeps its tasks

- **WHEN** a handler sends a checklist with a title and two tasks
- **THEN** the stored checklist carries that title and those two tasks

### Requirement: Synthesized values are valid and distinct

Synthesized content SHALL be schema-valid and distinguishable:

- every synthesized file SHALL get a unique id, and a file id the request passes SHALL be
  the stored one;
- a dice SHALL carry its emoji, 🎲 by default, and a value in that emoji's range;
- a string field aiogram enumerates SHALL take one of its values;
- a synthesized boolean SHALL be false, and a count of an empty list zero;
- every rich media block SHALL convert.

#### Scenario: Two uploads stay apart

- **WHEN** a handler uploads two different documents with their bytes
- **THEN** the two stored documents have different file ids, and each downloads its own
  bytes

#### Scenario: A dice is a dice

- **WHEN** a handler sends a dice without an emoji several times
- **THEN** each carries 🎲 and a value from 1 to 6

#### Scenario: A sticker is a regular sticker

- **WHEN** a handler sends a sticker
- **THEN** the stored sticker's type is one of the documented types, and it is not both
  animated and a video

### Requirement: Star transactions read like Telegram's

A star transaction SHALL report the payment's charge id as its id, a positive amount, and
the user on the other side as its source or receiver.

#### Scenario: A payment and its refund

- **WHEN** a user pays and the bot refunds the charge
- **THEN** the bot's transactions report the charge id, positive amounts, and the user as
  the payment's source and the refund's receiver

### Requirement: The bot can edit the administrators it promoted

An administrator the bot promoted SHALL report `can_be_edited` as true, and others as false.

#### Scenario: A promoted member is editable by the bot

- **WHEN** the bot promotes a member and reads them back
- **THEN** the member reports `can_be_edited` true

### Requirement: A declared world matches one built through the API

What a blueprint declares SHALL read back as the same state reached through API calls:
declared permissions SHALL apply the documented defaults, declared topics SHALL be created
by the bot, and a declared poll SHALL be stored on a message in its chat.

#### Scenario: Declared permissions follow their defaults

- **WHEN** a blueprint declares a restricted member allowed to send messages
- **THEN** the member reads back allowed to react, as the same restriction through the API
  does

#### Scenario: A declared poll is stored on a message

- **WHEN** a blueprint declares a poll in a chat
- **THEN** the chat holds a message carrying that poll, and users can vote in it

### Requirement: The bot edits only what Telegram lets it edit

An edit method SHALL refuse, as a Telegram error, a message the bot did not send outside a
channel or a business chat, a customer's message in a business chat, a forward, and a
business message addressed without its connection or a plain message addressed with one.
Every edit SHALL set `edit_date`, and the business account's 48-hour edit window SHALL bind
every edit method.

#### Scenario: A user's message cannot be edited by the bot

- **WHEN** a handler edits the text of a message a user sent in a group
- **THEN** the call raises `TelegramBadRequest`, and the message is unchanged

#### Scenario: An edit is dated

- **WHEN** the bot edits its own message
- **THEN** the returned and stored message carry an `edit_date`

### Requirement: Copies and forwards are new messages of their chat

A copy or forward SHALL be the bot's own message: it SHALL keep no reply, edit date,
protection, business connection, album, sender chat or sending details of the original, and
SHALL take only the keyboard its request passes. A forward SHALL keep the first origin of a
forwarded original. A copied poll SHALL be a poll of its own, which the bot can stop.

#### Scenario: A forward of a forward names the first origin

- **WHEN** the bot forwards a message a user forwarded to it
- **THEN** the new message's `forward_origin` names the original author

#### Scenario: A copied poll is separate

- **WHEN** the bot copies a poll and stops the copy
- **THEN** the original poll stays open

### Requirement: Channel posts are the channel's

A message the bot posts in a channel, a copy, a forward and a service message included,
SHALL carry the channel as `sender_chat` and no `from_user`.

#### Scenario: The bot posts in a channel

- **WHEN** a handler sends a message to a channel
- **THEN** the stored post has no `from_user`, and its `sender_chat` is the channel

### Requirement: A pin is announced

`pinChatMessage` SHALL post a `pinned_message` service message carrying the pinned message
without its own `reply_to_message`, in the pinned message's topic, once per pin.

#### Scenario: Pinning twice announces once

- **WHEN** a handler pins the same message twice
- **THEN** the chat holds one `pinned_message` service message for it

### Requirement: Dates count in whole seconds

A date or end date a bot passes SHALL be read in whole seconds and measured against the
clock's whole second, so an end computed from the current time is reached by advancing the
clock as far.

#### Scenario: A one-minute restriction ends after a minute

- **WHEN** a handler restricts a member until one minute from `datetime.now()`, and the test
  advances the clock by a minute
- **THEN** the member is no longer restricted

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

Routing diagnostics SHALL not report a handler that raised `SkipHandler` as the handler that
ran, nor record that exception as its error.

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

### Requirement: Membership triggers respect standing

A banned user's `join()`, `leave()` and `request_join()` SHALL fail as a setup error until
the ban ends, and a ban SHALL drop the user's pending join request. A `join()` by an
administrator or the owner already in the chat SHALL keep their status.

#### Scenario: A banned user cannot rejoin

- **WHEN** the bot bans a user and the user's actor joins
- **THEN** the trigger fails as a setup error, and the user stays banned

#### Scenario: Joining does not demote

- **WHEN** an administrator's actor joins the chat
- **THEN** the member is still an administrator with the same rights

### Requirement: Ephemeral messages can be waited for

A chat wait SHALL take a receiver and wait among the bot's ephemeral messages to that user,
and a wait on the shared history that times out SHALL say when the bot sent ephemeral
messages.

#### Scenario: Waiting for an ephemeral message

- **WHEN** a background task sends an ephemeral message to a user and the test waits with
  that receiver
- **THEN** the wait returns the message

### Requirement: Topic refusals use Telegram's wording

A send, copy or forward the bot makes into a thread the chat does not have SHALL fail with
`message thread not found`, whether the chat never had it or `deleteForumTopic` removed it,
as the Bot API server looks the topic up first. So SHALL one into thread 1 of a forum
supergroup, the General topic's id. A forum method naming a topic `deleteForumTopic` removed
SHALL fail with `TOPIC_DELETED`, and one naming a thread the chat never had with
`message thread not found`. Message 1 of a supergroup or a channel SHALL be reserved for
the chat's creation, so no topic SHALL be numbered 1. A topic a test or an actor names that
the chat lacks, or an actor bound to a topic deleted since, SHALL be a setup error that
names the topic, never a Telegram error.

#### Scenario: Posting into an unknown thread

- **WHEN** a handler sends a message with a thread id the forum never had
- **THEN** the call raises `TelegramBadRequest` with `message thread not found`

#### Scenario: Posting into a deleted topic

- **WHEN** a handler deletes a topic and then posts into it
- **THEN** the call raises `TelegramBadRequest` with `message thread not found`

#### Scenario: Closing a deleted topic

- **WHEN** a handler deletes a topic and then closes it
- **THEN** the call raises `TelegramBadRequest` with `TOPIC_DELETED`

#### Scenario: Posting into thread 1

- **WHEN** a handler sends a message with thread id 1 into a forum
- **THEN** the call raises `TelegramBadRequest` with `message thread not found`

#### Scenario: A test names an unknown topic

- **WHEN** a test binds an actor to a thread id the chat does not have
- **THEN** it raises `WorldLookupError` naming the topics the chat has

#### Scenario: An actor bound to a deleted topic

- **WHEN** an actor bound to a topic sends after the topic was deleted
- **THEN** it raises `WorldLookupError` saying the topic was deleted

### Requirement: A closed topic refuses those who cannot manage topics

A message the bot sends, copies or forwards into a closed topic, or into the General topic
while it is closed or hidden, SHALL fail with `TOPIC_CLOSED` unless the bot is the chat's
owner, an administrator holding `can_manage_topics`, or the topic's creator. A refused
message SHALL use no message id. User actors SHALL NOT be refused.

#### Scenario: A member bot posts into a closed topic

- **WHEN** the bot, a plain member, sends a message into a closed topic someone else
  created
- **THEN** the call raises `TelegramBadRequest` with `TOPIC_CLOSED`

#### Scenario: An administrator managing topics posts into it

- **WHEN** the bot holds `can_manage_topics` and sends into a closed topic
- **THEN** the message is stored in that topic

#### Scenario: The bot posts into its own closed topic

- **WHEN** the bot, a plain member, sends into a closed topic it created
- **THEN** the message is stored in that topic

#### Scenario: A hidden General topic

- **WHEN** the bot, a plain member, sends a message into a forum whose General topic is
  hidden
- **THEN** the call raises `TelegramBadRequest` with `TOPIC_CLOSED`

### Requirement: A topic message replies to the topic's root

A message stored in a supergroup's forum topic other than General that replies to no
message of its chat SHALL carry the topic's `forum_topic_created` service message as its
`reply_to_message`, and SHALL be marked as a topic message. This SHALL hold for the bot's
sends, copies, forwards and topic service messages and for messages a user actor sends. An
explicit reply SHALL keep its own target, and a reply in another chat SHALL still carry the
root. A replied message SHALL carry no `reply_to_message` of its own, for an actor's reply
as for the bot's. A private chat's topic SHALL give no implicit reply.

#### Scenario: A handler reads the topic name

- **WHEN** an actor bound to a topic sends a message
- **THEN** the handler receives it with `reply_to_message.forum_topic_created` naming the
  topic

#### Scenario: An explicit reply keeps its target

- **WHEN** the bot replies to a message inside a topic
- **THEN** the stored message replies to that message, not to the root

#### Scenario: An actor replies inside a topic

- **WHEN** an actor replies to a message in a topic, which replies to the root itself
- **THEN** the stored reply's `reply_to_message` is that message, carrying no reply of its
  own

#### Scenario: The General topic has no root

- **WHEN** the bot sends a message into the General topic of a forum
- **THEN** the stored message replies to nothing

### Requirement: The bot's own calls are checked against its rights

Unless the environment is built with `enforce_bot_rights=False`, a call the bot makes into
a group, a supergroup or a channel SHALL fail with Telegram's wording when the bot's
standing there does not allow it. The rules SHALL be one table from method type to the
right it takes, consulted once per call. Pinning and unpinning SHALL take
`can_pin_messages`, or `can_edit_messages` in a channel. Banning, unbanning and restricting
SHALL take `can_restrict_members`, and promoting `can_promote_members`. Changing the chat's
title, description or photo SHALL take `can_change_info`, and managing invite links and
join requests `can_invite_users`. Creating a topic SHALL take `can_manage_topics`, and so
SHALL editing, closing and reopening a topic the bot did not create and every General topic
method but unpinning; deleting a topic the bot did not create SHALL take
`can_delete_messages`. Deleting someone else's message SHALL take administrator status in
a basic group and `can_delete_messages` elsewhere. A send, copy or forward by a bot that is
not an administrator SHALL take the chat's permission for that kind of message, narrowed by
the bot's own restriction; a live location SHALL be refused as one, and paid media SHALL be
checked only when forwarded or copied, taking both `can_send_photos` and `can_send_videos`.
Posting into a channel SHALL take `can_post_messages`. The owner SHALL hold every right, and
the chat's permissions SHALL NOT grant the bot an administrator's right. A bot that was
removed from the chat or left it SHALL be refused every such call and every send with
`TelegramForbiddenError` and the Bot API server's text. Private chats and user actors SHALL
NOT be checked. With `enforce_bot_rights=False`, the bot SHALL hold every right.

#### Scenario: A member bot pins

- **WHEN** the bot, a plain member of a supergroup, pins a message
- **THEN** the call raises `TelegramBadRequest` with
  `not enough rights to manage pinned messages in the chat`

#### Scenario: A member bot bans

- **WHEN** the bot, a plain member of a supergroup, bans a user
- **THEN** the call raises `TelegramBadRequest` with
  `not enough rights to restrict/unrestrict chat member`, and the user stays

#### Scenario: A member bot renames the chat

- **WHEN** the bot, a plain member of a group, sets the chat's title
- **THEN** the call raises `TelegramBadRequest` with
  `not enough rights to change chat title`

#### Scenario: The bot closes its own topic

- **WHEN** the bot, a plain member of a forum, closes a topic it created
- **THEN** the topic closes, while closing a topic someone else created raises
  `TelegramBadRequest` with `not enough rights to close or open the topic`

#### Scenario: A member bot sends into a silenced chat

- **WHEN** the chat's permissions forbid text and the bot, a plain member, sends text
- **THEN** the call raises `TelegramBadRequest` with
  `not enough rights to send text messages to the chat`, while a user actor's message in
  the same chat is still delivered

#### Scenario: A kicked bot sends

- **WHEN** the bot's status in a supergroup is kicked and it sends a message there
- **THEN** the call raises `TelegramForbiddenError` with
  `Forbidden: bot was kicked from the supergroup chat`, and nothing is stored

#### Scenario: Opting out

- **WHEN** the environment is built with `enforce_bot_rights=False`
- **THEN** the same bot pins, bans and sends as if it held every right

### Requirement: The owner can turn a forum's topics off and on

A user actor who owns a supergroup SHALL be able to turn its topics off and on. No update
SHALL be delivered for it. Turning topics off SHALL keep them, and turning them on again
SHALL restore them as they were. While topics are off, the forum methods SHALL fail with
`the chat is not a forum`, and a message the bot sends with a thread id SHALL be stored
without one, which is an assumption the Bot API does not document. A blueprint SHALL be
able to declare a supergroup a forum before it has any topic. Anyone but the owner, or a
chat other than a supergroup, SHALL be a setup error.

#### Scenario: A stale thread id after topics are off

- **WHEN** the owner turns topics off and the bot sends into a former topic's thread id
- **THEN** the message is stored in the chat with no thread id, not as a topic message

#### Scenario: Turning topics on again

- **WHEN** the owner turns topics back on
- **THEN** the former topics exist again, and a message sent into one is tagged with it

#### Scenario: Someone else tries

- **WHEN** a member who is not the owner turns topics off
- **THEN** the trigger raises `WorldLookupError`, and the chat is still a forum

### Requirement: Flood limits can be modeled per chat

An environment built with `rate_limits` SHALL refuse a message-producing call into a chat
that is over a limit with error 429, `Too Many Requests: retry after N`, and a
`TelegramRetryAfter` whose `retry_after` is the whole seconds until a send into that chat is
allowed. The default limits SHALL be one message per second in any chat and 20 per minute
in a group or supergroup, counted for the whole chat across its topics. The limits SHALL be
read only after the checks Telegram makes before sending, so a call refused for the bot's
rights, its thread or the message it replies to SHALL fail with that refusal, and a refused
call SHALL change nothing. The counted methods SHALL be the modeled sends, read off the
modeling registry. A call SHALL be counted once it succeeds, a media group or batch once.
The limits SHALL be read off the event loop's clock plus the time `advance_time` moved.
Without `rate_limits` nothing SHALL be limited.

#### Scenario: Two messages in one second

- **WHEN** limits are on and the bot sends two messages into a chat at the same moment
- **THEN** the second raises `TelegramRetryAfter` with `retry_after` 1, and is not stored

#### Scenario: A refusal Telegram makes first

- **WHEN** the chat is over its limit and the bot sends into a thread it does not have
- **THEN** the call raises `TelegramBadRequest` with `message thread not found`

#### Scenario: Waiting out the refusal

- **WHEN** the test advances the time by that `retry_after`
- **THEN** the next send into the chat goes through

#### Scenario: A busy forum

- **WHEN** the bot sends 20 messages within a minute into two topics of one group
- **THEN** the 21st raises `TelegramRetryAfter`

### Requirement: The bot's background tasks can be waited for

`wait_for_background_tasks()` SHALL wait, cancelling nothing, until every task the environment counts
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

### Requirement: Every route of a test is kept and can be checked

An environment SHALL keep the route record of every update it routed for its whole life,
readable as `all_routes`. `assert_updates_handled()` SHALL fail on every trigger none of
whose updates was handled and on every update that raised, even if an error handler
swallowed it, listing each with its description, except for a trigger the test passed to
`assert_unhandled()`. `assert_unhandled()` SHALL apply to the trigger `routes` reports,
SHALL fail if that trigger has nothing the check would flag, and SHALL return what it would
flag. With the `bot_env_assert_updates_handled` fixture returning true, the plugin SHALL run
the check after each test that passed, failing that test.

#### Scenario: An update in the middle of a game went nowhere

- **WHEN** a test feeds a handled update, an unhandled one, and a handled one
- **THEN** `all_routes` holds all three, and `assert_updates_handled()` fails naming the
  unhandled one

#### Scenario: A join whose service message nobody claims

- **WHEN** a trigger feeds a handled update and an unhandled one
- **THEN** `assert_updates_handled()` passes

#### Scenario: An update the test meant the bot to ignore

- **WHEN** a test calls `assert_unhandled()` after an unhandled trigger
- **THEN** `assert_updates_handled()` passes

#### Scenario: The plugin checks a passing test

- **WHEN** the fixture flag is on and a passing test left an update unhandled
- **THEN** that test fails, and a test that called `assert_unhandled()` passes

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

### Requirement: The documentation shows fast sleeps that keep the loop's clock real

The documentation SHALL show how a suite that keeps real database drivers speeds up a bot's
own sleeps without replacing the event loop's clock, SHALL say why `looptime` and such
drivers clash, and SHALL say that the toolkit has no time control mode of its own. The code
it shows SHALL run as written.

#### Scenario: The recipe as written

- **WHEN** the recipe's code blocks are written into a project and its tests run
- **THEN** they pass, the fifteen-second pause takes under a second, and `asyncio.sleep`
  and the loop's clock are untouched

### Requirement: A user actor can manage the topics of a forum

A user actor SHALL be able to create a topic, close, reopen and delete one, hide and unhide
the General topic, and close and reopen it. Each SHALL change the world as the matching bot
method does, by the same code, and SHALL store and feed the service message Telegram posts
for it, from that user: `forum_topic_created`, `forum_topic_closed`, `forum_topic_reopened`,
`general_forum_topic_hidden` or `general_forum_topic_unhidden`, and `forum_topic_closed` or
`forum_topic_reopened` for the General topic. Deleting a topic SHALL feed nothing, as
Telegram posts no message for it. A topic deleted since an actor was bound to it SHALL be a
setup error, never a Telegram error.
A topic SHALL be named as a declaration, a state or a thread id, and default to the topic the
actor is bound to. The actor SHALL hold `can_manage_topics` in a chat that is a forum,
whatever `enforce_bot_rights` says: as the owner or an administrator granted it, or, to
create a topic, as the chat's permission of that name, which SHALL bind administrators as
much as members and SHALL be narrowed by the actor's own restriction. The creator of a topic
SHALL close, reopen and delete it without the right. Otherwise the trigger SHALL raise
`WorldLookupError` naming the right and how to grant it, and change nothing.

#### Scenario: The owner closes a topic

- **WHEN** the owner of a forum closes one of its topics
- **THEN** the topic is closed and a `forum_topic_closed` message from the owner, in the
  topic and replying to its root, is stored and handled by the dispatcher

#### Scenario: Deleting a topic

- **WHEN** an administrator with `can_manage_topics` deletes a topic
- **THEN** the topic and its messages are gone, nothing is fed, and a later bot call into the
  thread fails with `message thread not found`

#### Scenario: A member the chat lets create topics

- **WHEN** the chat's permissions grant `can_manage_topics` and a plain member creates a topic
- **THEN** the topic exists with that member as its creator, who may then close, reopen and
  delete it

#### Scenario: A member without the right

- **WHEN** a plain member creates a topic in a chat whose permissions deny `can_manage_topics`
- **THEN** `WorldLookupError` names `can_manage_topics` and how to grant it, and no topic or
  message is added

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

The environment SHALL note the tasks it tracks weakly, and SHALL keep no task that succeeded
or was cancelled once it ends. A task that failed SHALL be kept until its exception is
retrieved, by the bot or by a report, so that `wait_for_background_tasks()` and `drain()` still raise
`BackgroundTaskError` and `DrainedTaskError` for a failure nobody retrieved, and SHALL NOT
for one the bot retrieved, however late. Retrieved failures SHALL be let go when the tasks
are next counted rather than each time a task ends. A disposed environment SHALL hold no
task.

#### Scenario: Many short tasks

- **WHEN** the bot spawns two hundred tasks that each finish
- **THEN** the environment holds none of them, and none is kept alive by it

#### Scenario: A failure among them

- **WHEN** one of many finished tasks failed and nobody retrieved why
- **THEN** `wait_for_background_tasks()` raises `BackgroundTaskError` naming it, with its exception as the
  cause, and afterwards the environment holds nothing

#### Scenario: A failure the bot handled

- **WHEN** the bot awaits a task that failed, and catches the exception, at any later time
- **THEN** neither `wait_for_background_tasks()` nor `drain()` reports it
