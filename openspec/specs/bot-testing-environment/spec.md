# bot-testing-environment Specification

## Purpose

The stateful fake Telegram that `aiogram.test` runs bots against: a declarative blueprint
describing a world of chats, users, members, topics, business connections and communities;
isolated environments materialized from it; actors that trigger real updates through the
real dispatcher; and Bot API interception that applies modeled calls to world state,
answers everything else with a schema-valid synthesized result, and records every call for
assertion.
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

### Requirement: Telegram errors behave like production errors

Errors produced by the environment — whether from modeling rules, from a declared
override, or from an invalid operation such as editing a deleted message — SHALL be
raised as the framework's own exception types from `aiogram.exceptions`, carrying a
description, so error handlers and `except` blocks under test behave as they do against
real Telegram.

#### Scenario: Invalid operation raises a framework exception

- **WHEN** a handler edits a message that no longer exists
- **THEN** `TelegramBadRequest` is raised with a description explaining the failure

#### Scenario: Registered error handlers receive the exception

- **WHEN** the dispatcher has an error handler and an intercepted call raises
- **THEN** the error handler runs through the normal dispatcher error pipeline

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
- **THEN** the call fails with the framework's own error type rather than a synthesized
  connection

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
message is unknown or deleted, and when the target is an inline message, matching the
behavior of the already-modeled text and caption edits.

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
- **THEN** the call raises `TelegramBadRequest` naming inline messages as unmodeled,
  rather than silently succeeding

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
tag belongs to a regular member.

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
environment recorded, debit the bot's balance, and mark the charge refunded. Refunding an
unknown charge, or one already refunded, SHALL raise `TelegramBadRequest`.

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
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Star subscriptions can be cancelled and re-enabled

`editUserStarSubscription` SHALL act on the subscription behind a recorded charge, and the
environment SHALL reflect whether that subscription is cancelled.

#### Scenario: Cancelling a subscription

- **WHEN** a handler cancels the subscription behind a charge it received
- **THEN** the environment reports that subscription as cancelled, and re-enabling it
  reverses that

#### Scenario: Acting on an unknown subscription fails

- **WHEN** a handler cancels a subscription for a charge the environment does not know
- **THEN** the call raises `TelegramBadRequest`

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
- **THEN** the call raises `TelegramBadRequest`

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
SHALL be applied to that registry, and `getStickerSet` SHALL report the result. Each SHALL
fail with `TelegramBadRequest` where Telegram would: a name already taken, a set that does
not exist, or a sticker that is not in the set.

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
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Removing a sticker that is not in the set fails

- **WHEN** a handler deletes or replaces a sticker the set does not contain
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Deleting a set removes it

- **WHEN** a handler deletes a set and then reads it
- **THEN** the read raises `TelegramBadRequest`

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
