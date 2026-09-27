## Why

`aiogram.test` shipped with a bounded world model — chats, users, members, messages — and
everything outside it degrades to record-and-synthesize. That was the right first cut, but
three Bot API surfaces are common enough that a real bot cannot be tested without them,
and today they fail *quietly* rather than loudly:

- **Forum topics.** `env.state()` resolves the FSM context without a thread id, so under
  `FSMStrategy.USER_IN_TOPIC` / `CHAT_TOPIC` it returns a different key than the one the
  dispatcher just wrote to. Measured on the current implementation: the handler's key
  carried `thread_id=77`, `env.state()` returned `thread_id=None`, and the data the
  handler had just stored read back as `{}`. A test asserting on FSM data in a forum chat
  passes or fails for the wrong reason. There is also no way to address a topic — a test
  must reach for the raw `fields={"message_thread_id": …}` escape hatch — and all 13
  forum methods are unmodeled, so creating a topic returns a `ForumTopic` unrelated to the
  chat and closing one changes nothing.
- **Business connections.** None of the four business update types
  (`business_connection`, `business_message`, `edited_business_message`,
  `deleted_business_messages`) has an actor trigger; testing a business bot means
  hand-assembling `Update` objects and calling a private helper. Worse, a message sent
  with `business_connection_id` is stored as sent *by the bot*, while real Telegram sends
  it as the business account — so an assertion about the sender is green against behavior
  that never happens in production.
- **Communities.** `Community`, `CommunityChatAdded` and `CommunityChatRemoved` exist with
  no way to declare a community or trigger its service messages, so the Bot API 10.2
  handlers most bots are about to write have no test path at all.

## What Changes

- **Forum topics as world state.** Topics are declared on a blueprint
  (`blueprint.add_topic(chat, "Support")`, `Chat.is_forum` set automatically) and are
  created, edited, closed, reopened and deleted by the real forum methods, each emitting
  the matching service message into the chat. Messages carry `message_thread_id` and
  `is_topic_message`, and each topic keeps its own thread of messages.
- **Topic addressing for actors.** `user.in_(chat, topic=support)` binds an actor to a
  topic; every trigger it produces is threaded correctly, and `message.answer()` keeps
  replying inside the topic as it does in production.
- **Correct FSM keys.** `env.state()` accepts `topic=` and `business_connection=` and
  resolves through the dispatcher's strategy, so the key it returns is the key the
  handler used. This closes the silent wrong-answer defect above.
- **Business connections as world state.** A blueprint declares connections
  (`blueprint.add_business_connection(owner, can_reply=True)`) carrying the owner, the
  `user_chat_id`, `is_enabled` and `BusinessBotRights`. `GetBusinessConnection` answers
  from that state; `ReadBusinessMessage` and `DeleteBusinessMessages` are applied to it.
- **Business sender attribution.** A message sent with a `business_connection_id` is
  stored as sent by the **business account user**, with `sender_business_bot` set to the
  bot — matching what the customer actually sees.
- **Business actor triggers.** `business_message`, `edited_business_message`,
  `business_connection` (enabled/disabled) and `deleted_business_messages`.
- **Communities.** Declared on a blueprint and attached to chats, surfaced through
  `ChatFullInfo.community`, with actor triggers for the `community_chat_added` and
  `community_chat_removed` service messages.

No breaking changes: every new capability is an added parameter or a new method.

## Capabilities

### New Capabilities

None. This extends the world model introduced by `add-bot-testing-toolkit`.

### Modified Capabilities

- `bot-testing-environment`: the modeled surface grows to cover forum topics, business
  connections and communities; actors gain topic binding and business/community triggers;
  and the FSM-context requirement is corrected to resolve keys with the thread and
  business connection, which it currently ignores.

## Impact

- **Depends on** `add-bot-testing-toolkit` — this change edits the package that change
  introduces, and its delta spec assumes those requirements are in place. Archive that
  change first, or archive them in order.
- **Code**: `aiogram/test/world.py` (topic, business connection and community state),
  `blueprint.py` (declarations), `actors.py` (topic binding, new triggers),
  `modeling.py` (13 forum methods, business methods, business sender attribution),
  `environment.py` (`state()` signature and resolution).
- **Tests**: new modules under `tests/test_testing/`, holding the package at 100%.
  The synthesis guard over every generated return type stays the backstop for everything
  still unmodeled.
- **Docs**: new sections in `docs/dispatcher/testing.rst` for topics, business connections
  and communities, plus the corrected FSM guidance.
- **Changelog**: `CHANGES/<issue-or-pr>.feature.rst`.
- **Compatibility**: no new dependencies; Python 3.10–3.14 and PyPy 3.11 as before.
- **Risk**: the modeled surface roughly doubles, and every modeled method is a fidelity
  claim the fake now has to keep. Anything not explicitly modeled must keep degrading to
  record-and-synthesize rather than guessing semantics.
