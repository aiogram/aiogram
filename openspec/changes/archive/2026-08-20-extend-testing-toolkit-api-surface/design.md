## Context

This extends the toolkit from `add-bot-testing-toolkit`; its decisions D1–D10 (session
interception, typed `Default` resolution, the override → model → synthesize ladder, frozen
API types, blueprint materialization, dispatcher storage swapping) all still hold. What
changes is the size of tier 2 — the modeled surface.

Facts measured against the current implementation rather than assumed:

- `FSMContextMiddleware.resolve_context(bot, chat_id, user_id, thread_id,
  business_connection_id, destiny)` **already accepts** everything needed;
  `BotTestEnvironment.state()` simply never passes the last two. `apply_strategy` consumes
  `thread_id` only for `USER_IN_TOPIC` and `CHAT_TOPIC`, so forwarding it unconditionally
  is safe for every other strategy.
- Business updates already route correctly once an `Update` is built by hand — a probe fed
  a `business_message` and the handler received both the message's connection id and a
  matching FSM key. The gap is ergonomics and state, not dispatching.
- `Chat.is_forum` exists. `ForumTopic` carries `message_thread_id`, `name`, `icon_color`,
  `icon_custom_emoji_id`, `is_name_implicit`. `BusinessConnection` carries `id`, `user`,
  `user_chat_id`, `date`, `is_enabled`, `rights`, `can_reply`.
- Communities have **no methods at all** — only the `Community` type, the two service
  message fields on `Message`, and `ChatFullInfo.community`. Their whole surface is
  declaration plus service messages.

## Goals / Non-Goals

**Goals:**

- Make forum, business and community bots testable without raw `Update` assembly or the
  `fields=` escape hatch.
- Return FSM keys that match what the dispatcher used, under every strategy.
- Keep the modeled boundary explicit, and keep everything outside it degrading to
  record-and-synthesize.

**Non-Goals:**

- Enforcing business rights (`can_reply`, `BusinessBotRights`) as permission errors. The
  fake models shape, not policy — a bot that replies without the right succeeds here.
- Direct messages topics (`DirectMessagesTopic`, `direct_messages_topic_id`). A separate
  concept, deliberately deferred.
- Topic permissions, `can_manage_topics` enforcement, or icon sticker validation.
- Community membership rules or any community method — Telegram exposes none.

## Decisions

### D11. Topics are a registry on the chat; messages stay in one list

`ChatState` gains `topics: dict[int, TopicState]` and `is_forum`. A `TopicState` holds its
thread id, name, icon fields, and `is_closed`. Messages continue to live in the single
`ChatState.messages` list — `topic.messages` is a **filtered view** over it by
`message_thread_id`.

Two parallel lists would be the obvious alternative and the wrong one: every edit, delete,
forward and pin would have to keep both in step, and any missed path produces a chat whose
topic view disagrees with itself. A view cannot drift.

### D12. A topic's thread id is its creation service message id

Telegram numbers a forum topic by the message id of the `forum_topic_created` service
message that opened it. The model does the same: `create_forum_topic` allocates a message
id from the chat, emits the service message, and uses that id as the topic's
`message_thread_id`. Blueprint-declared topics are materialized the same way, so a
declared world is indistinguishable from one built by API calls.

The General topic is modeled as a `TopicState` flagged `is_general`, whose messages carry
no `message_thread_id` — matching Telegram, where General posts are untagged. The
`*GeneralForumTopic*` methods act on it.

### D13. Unknown topics fail loudly

Posting into a `message_thread_id` that does not exist in a forum chat raises the
framework's `TelegramBadRequest`, rather than silently creating the topic or accepting the
tag. Silent acceptance is exactly the failure mode this change exists to remove; a typo'd
thread id must not produce a green test.

### D14. Business connections are world state keyed by connection id

`World` gains `business_connections: dict[str, BusinessConnectionState]` holding the owner
user id, `user_chat_id`, `is_enabled`, `can_reply` and rights. `GetBusinessConnection`
answers from it; an unknown id fails rather than synthesizing a connection that no test
declared.

### D15. Sender attribution is resolved at message build time

`build_message` gains one branch: if the method carries a `business_connection_id` known to
the world, the stored message's `from_user` becomes the connection owner and
`sender_business_bot` becomes the bot. Everything else about the send path is unchanged.

This is the decision with the most user-visible consequence — it is what makes
`chat.messages[-1].from_user` mean "what the customer sees" — and it costs one lookup.

### D16. The actor binding decides the update kind

`user.in_(chat, topic=…)` and `user.in_(chat, business=…)` return new bound actors, keeping
the existing "binding is a value, not state" rule (D8). The binding then selects what
`send()`/`edit()` produce: a `message`, a topic-tagged `message`, or a `business_message`.

The alternative — separate `send_business()` / `send_in_topic()` methods — multiplies the
trigger surface by the binding dimensions and makes every future update kind a
combinatorial addition.

### D17. Chat-level events stay on the actor

Community service messages (`community_chat_added` / `community_chat_removed`) and
connection enable/disable are triggered through the actor that performed them
(`actor.add_chat_to_community(community)`, `actor.disable_business_connection()`), so
`event_from_user` resolves the way it does for every other trigger. Forum service messages
are **not** triggers: they are emitted as a side effect of the modeled forum methods, since
in production only the API produces them.

### D18. `state()` gains keyword-only parameters

`env.state(user, chat=None, *, topic=None, business_connection=None)` forwards `thread_id`
and `business_connection_id` into `resolve_context`. Keyword-only keeps every existing call
site valid. When the actor is bound, `actor.state()` fills them from the binding, which is
the path most tests will use and the one that cannot be got wrong.

## Risks / Trade-offs

- **The modeled surface roughly doubles, and each modeled method is a fidelity promise.**
  → Keep the list explicit in the spec, keep unmodeled methods on the synthesize path, and
  add each new method with a test that asserts the resulting *state*, not just the return
  value.
- **General-topic semantics are subtle** (untagged messages, a separate method family). A
  wrong model here produces confidently wrong tests for the most common forum chat. → Model
  it explicitly as a flagged topic rather than as "topic id 1", and cover posting to
  General, closing it, and hiding/unhiding it.
- **Business attribution changes what existing assertions see.** A test written against the
  current behavior that asserts `from_user` is the bot on a business message will start
  failing — correctly, but visibly. → Call it out in the changelog; the toolkit is new
  enough that the blast radius is small, and the old behavior was wrong.
- **Rights are declared but not enforced (non-goal).** A reader may reasonably expect
  `can_reply=False` to produce an error. → Document the boundary in the same place the
  declaration is documented.
- **Topic-filtered views are O(n) per access.** Fine for test-sized chats; a chat with
  thousands of messages in one test would notice. → Accept; revisit only if a real suite
  shows it.

## Migration Plan

Purely additive except for business sender attribution (D15), which corrects behavior
rather than extending it. Rollout: land the world/blueprint changes, then the modeled
methods, then the triggers, then documentation. Rollback is reverting the change — nothing
outside `aiogram/test` depends on it.

## Open Questions

- Should `can_reply=False` eventually raise on a business send, as a deliberate exception
  to the "shape, not policy" rule? It is the one business right a bot author is likely to
  branch on.
- Do direct messages topics belong in a follow-up, or folded into topic addressing once
  their Bot API surface settles?
- Should `env.state()` warn when called without a topic on a topic-aware strategy, instead
  of silently resolving the chat-level key? A warning would have caught the original defect
  at the call site.
