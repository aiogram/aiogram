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

The environment SHALL report where the most recently fed update actually went, distinct
from whatever value the trigger call returned: whether the dispatcher considered it
handled, which handler and which router claimed it, and the first exception raised inside
the middleware chain or the handler — captured where it was raised even when something
further out, such as the framework's own error-handling middleware, goes on to swallow it.
"Handled" SHALL follow the dispatcher's own definition — something other than "unhandled"
came back — which a middleware that returns without calling the next one already satisfies;
the winning handler's identity SHALL be reported separately, since it is the only field
that says whether a handler actually ran. This report SHALL be cleared at the start of
every fed update and set once that update finishes routing, and SHALL be absent until the
first update is fed.

The environment SHALL also provide an assertion spelled directly against this report,
matched by a substring of the winning handler's qualified name, which SHALL fail naming
where the update actually went — including the captured exception, if there was one —
rather than only stating that the named handler did not run.

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

#### Scenario: The assertion fails naming where the update actually went

- **WHEN** a test asserts the update was handled by a name that does not match the winning
  handler
- **THEN** the failure names the handler and router that actually claimed it, including any
  captured exception

#### Scenario: The report resets between updates

- **WHEN** a second update is fed after a first one was handled
- **THEN** the report reflects only the second update's routing, not anything left over from
  the first

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
demotion — there is no way through this trigger to "explicitly grant nothing." Demoting
SHALL drop the subject to a plain member and clear both the granted rights and the custom
title, while leaving the subject's tag untouched. Both SHALL refuse to act on the chat's
owner, the same refusal `promoteChatMember` itself gives.

#### Scenario: Promoting with no subject promotes the bot

- **WHEN** an actor calls the promotion trigger with no subject and at least one right
- **THEN** the bot's own membership becomes administrator, carrying exactly the rights named

#### Scenario: Promoting with no rights at all still promotes

- **WHEN** an actor calls the promotion trigger naming no rights
- **THEN** the subject becomes an administrator with every right denied, rather than being
  read as a demotion

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

The environment SHALL provide a named recipe for making every delivery into one chat fail
the way a real block does — covering every method that delivers content into a chat, not
only the single most common one — under the same handle-and-scoping rules as a general
override, but carrying no call-count budget: it SHALL hold for as long as it is in force
rather than for a fixed number of calls.

A call SHALL be recorded in the call log **before** any override is consulted for it, so
that a test can assert both that the call was made — reaching the right addressee with the
right content — and separately assert on how an override answered it.

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

#### Scenario: Two recipients can be blocked independently

- **WHEN** a test declares the blocked-chat recipe for two different chat ids at once
- **THEN** both chats' deliveries fail, and a message to a third, unblocked chat still
  succeeds, regardless of which chat a handler happens to message first

#### Scenario: A refused call is still visible in the call log

- **WHEN** a call is answered by an override that raises
- **THEN** the call log still holds the call as the code under test built it, so a test can
  assert on the addressee and content of a call that was refused

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
Assigning a *plain mapping* SHALL still be wrapped into a fresh registry wired to this world.
Assigning another world's **live** chat registry SHALL instead be refused: a registry holds
the donor's own `ChatState` objects rather than copies, so installing it here would rewrite
`chat.world` on the objects the donor still holds, silently binding the donor's own chats —
and everything they store afterwards — to this world's bot instead. A registry already wired
to *this* world SHALL be left alone by identity, so re-assigning a world's own `chats` to
itself SHALL stay a no-op.

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

#### Scenario: Sharing chats across worlds is still possible, explicitly

- **WHEN** a test assigns a plain `dict` copy of one world's chats — `dict(other.chats)` —
  to another world's `chats` attribute
- **THEN** the same `ChatState` objects are shared, but now wired to the receiving world, and
  a chat added afterwards through either world's registry is bound to that world alone

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

The condition wait SHALL accept one chat or topic, or several, whose contents are appended
to the timeout message when it gives up — because the condition is a lambda over state the
failure cannot otherwise describe, while what the bot posted instead is usually the answer.

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

The environment SHALL provide a wait that polls several chats together and returns once
**every** one of them holds a matching message, rather than requiring a test to await each
chat's own message wait in turn. It SHALL accept chats named by declaration, by resolved
state, or by bare id, mixed freely, and SHALL apply the same newest-match rule a single
chat's own message wait applies. A timeout SHALL name only the chats still missing a match,
not the ones that already have one.

#### Scenario: A broadcast wait returns once every chat has a match

- **WHEN** a handler messages several chats from one trigger and a test waits across all of
  their ids at once
- **THEN** the wait returns a result keyed by chat id, once every named chat holds a message
  satisfying the predicate

#### Scenario: Mixed forms of naming a chat are accepted

- **WHEN** the chats passed to the broadcast wait mix a blueprint declaration, a resolved
  chat state and a bare id
- **THEN** all three resolve to their chats and are waited on together

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
test's own; a task already running when the environment was built SHALL be left alone. A
task that does not finish within a stated timeout after being cancelled SHALL fail loudly
rather than being abandoned a second time. This SHALL NOT be invoked automatically by
environment teardown, since teardown has both an asynchronous and a synchronous path and an
automatic drain would behave differently between them, and since cancelling tasks a test
never mentioned as an invisible side effect of teardown would obscure a stopped background
process as a mystery rather than a stated outcome.

#### Scenario: Tasks the test left running are cancelled and awaited

- **WHEN** a trigger schedules a background task that is still running when the test asks to
  drain, with a timeout that comfortably exceeds what cancellation takes
- **THEN** the task is cancelled, awaited, and counted in the number returned

#### Scenario: A task present before the environment was built is left alone

- **WHEN** a task was already running before the environment was constructed
- **THEN** draining does not cancel it and does not count it

#### Scenario: A task that outlives its cancellation fails loudly

- **WHEN** a task swallows its own cancellation and is still running after the stated
  timeout
- **THEN** draining raises, naming the task, rather than abandoning it silently

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
into the chat where Telegram would.

#### Scenario: Creating a topic

- **WHEN** a handler calls `createForumTopic`
- **THEN** the returned topic exists in the chat with the requested name, and a
  `forum_topic_created` service message appears in the chat

#### Scenario: Closing and reopening a topic

- **WHEN** a handler closes a topic and later reopens it
- **THEN** the topic's state follows, and `forum_topic_closed` and `forum_topic_reopened`
  service messages are appended in order

#### Scenario: Editing a topic

- **WHEN** a handler edits a topic's name or icon
- **THEN** the stored topic reflects the change and a `forum_topic_edited` service message
  is emitted

#### Scenario: Deleting a topic

- **WHEN** a handler deletes a topic
- **THEN** the topic and its messages are gone from the chat, and a later attempt to post
  into it fails with the error Telegram would return

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
query SHALL succeed and clear it, and answering an unknown or already-answered identifier
SHALL raise `TelegramBadRequest`, as Telegram does when a query has expired or was already
answered.

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
the votes cast, and whether it is closed. A blueprint SHALL be able to declare an existing
poll.

#### Scenario: A sent poll is stored on its message

- **WHEN** a handler calls `sendPoll`
- **THEN** a message carrying that poll is appended to the chat, and the returned message
  is the stored one

#### Scenario: A declared poll is answerable

- **WHEN** a blueprint declares a poll in a chat and a user actor votes in it
- **THEN** the vote is recorded without the poll having been sent through the API first

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

### Requirement: Permissions are stored but not enforced

The environment SHALL store chat permissions and member restrictions without enforcing
them: a call that Telegram would reject for want of a right SHALL still succeed in the
fake. The toolkit models the shape of administration, not its policy.

#### Scenario: Restricted sending still succeeds

- **WHEN** a chat's permissions forbid sending messages and a handler sends one anyway
- **THEN** the message is appended to the chat as usual, and a test that needs the
  rejection declares it with an override

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
