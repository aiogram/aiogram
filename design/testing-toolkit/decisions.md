# Decisions

Why `aiogram.test` is built the way it is. The OpenSpec change sets this was distilled from
were removed with the 3.x release of the toolkit; they stay in the history of `feature/testing`
(PR #1887). Each decision was checked against the code at the time of writing.

Code comments cite these as "design decision TW-<n>". IDs are stable: do not renumber. A new
decision gets the next free number, in whichever section it belongs; a decision that stops
holding moves to "Superseded" with the reason, keeping its ID.

Format: **Decision**, **Why**, **Rejected** (alternatives the design considered), **Code**,
**Source** (the archived change-set folder).

## Core architecture

### TW-1 Intercept at the session, not by patching `Bot`
**Decision:** `FakeTelegramSession(BaseSession)` implements `make_request` and sends every call to the environment. `Bot`, shortcuts and `bot.__call__` stay as they are.
**Why:** `make_request` is the one point every Bot API call goes through. Shortcuts, middlewares and error conversion then behave as in production.
**Rejected:**
- Monkeypatching `Bot.__call__`: code holding a bound method never sees the patch, and the framework's own error conversion is bypassed.
**Code:** `aiogram/test/session.py` `FakeTelegramSession.make_request`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-2 Resolve `Default` sentinels into typed objects before anything sees the call
**Decision:** `resolve_defaults` replaces every `Default` with `bot.default[name]` and rebuilds models with `model_copy(update=...)`. The call log and the world both get the resolved object.
**Why:** `prepare_value` resolves defaults only during serialization, which a fake session never reaches. `prepare_value` also flattens to JSON and loses the typed objects tests assert on.
**Rejected:**
- Reusing `prepare_value`: it destroys the types. The cost is a second resolver, and a guard test asserts both agree for every method with a `Default` field.
**Code:** `aiogram/test/defaults.py` `resolve_defaults`; called from `aiogram/test/environment.py` `BotTestEnvironment.handle_call`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-3 Every call goes through override, then model, then synthesize
**Decision:** `handle_call` tries a test-declared override first, then a registered handler, then synthesizes a schema-valid `__returning__`. The modeled set is an explicit registry.
**Why:** Tier 3 makes the toolkit survive Bot API bumps: a new generated method gets a valid answer with no change here. Keeping tier 2 an explicit list makes its growth a deliberate decision.
**Rejected:**
- Requiring registration for every method (the `tests/mocked_bot.py` style): a bot that calls `getChatMember` in a filter would need it registered in every test.
**Code:** `aiogram/test/environment.py` `BotTestEnvironment.handle_call`; `aiogram/test/modeling.py` `REGISTRY`, `models`, `find_handler`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-4 The call is recorded before overrides are consulted
**Decision:** `handle_call` records the resolved method in `env.calls`, then makes a `detached_copy` for everything downstream.
**Why:** A refused call is still a call the bot made, so a test can assert both what the bot tried and how it coped. Copying once at the choke point means no handler needs its own copy.
**Code:** `aiogram/test/environment.py` `BotTestEnvironment.handle_call`; `aiogram/test/calls.py` `CallLog`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-5 World state is plain mutable dataclasses, converted at the boundary
**Decision:** The world holds `ChatState`, `UserState`, `MemberState` and friends as mutable dataclasses and converts them to `aiogram.types` objects on read. `message_id` is allocated per chat; `update_id` is global and monotonic.
**Why:** Frozen pydantic types would need a rebuild on every edit and make identity tracking awkward. Per-chat ids match Telegram's numbering.
**Code:** `aiogram/test/world.py` `World`, `ChatState`, `MemberState`, `ChatState.allocate_message_id`, `World.last_update_id`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-6 A blueprint holds no runtime state; `build()` deep-copies it
**Decision:** `Blueprint` is a declaration. `Blueprint.build()` deep-copies it and materializes a fresh `World`.
**Why:** Isolation is then structural. A blueprint shared at session scope has nothing mutable to leak, so no teardown or snapshot machinery is needed.
**Code:** `aiogram/test/blueprint.py` `Blueprint`, `Blueprint.build`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-7 Reuse the project's dispatcher; swap its storage and workflow data
**Decision:** The dispatcher may have any scope. The environment installs a fresh `MemoryStorage` and saves `workflow_data`, then restores both on dispose in a `finally`. For projects that do build a dispatcher per test, `detach_router(router)` clears the router's `_parent_router` so it can be included again.
**Why:** A `Router` can be attached to one parent once, and real bots declare routers at import time. A fresh dispatcher per test fails on the second test.
**Rejected:**
- Forcing a function-scoped dispatcher: it breaks the common `router = Router()` module pattern, and the first thing a user sees is a `RuntimeError`.
**Code:** `aiogram/test/environment.py` `BotTestEnvironment.__init__`, `dispose`, `dispose_sync`; `aiogram/test/routing.py` `detach_router`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-8 `aiogram.test` is hand-written and must not import pytest at package level
**Decision:** The package lives outside the `butcher` boundary. Only `plugin.py` imports pytest. Everything a fixture gives is also importable directly.
**Why:** The toolkit is usable outside pytest, and importing `aiogram.test` must not need the `test` extra.
**Rejected:**
- `aiogram.testing` as the name: slightly more readable. `aiogram.test` was chosen for brevity.
**Code:** `aiogram/test/__init__.py`; `aiogram/test/plugin.py`; `pyproject.toml` extra `test`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-9 One rule for values entering the world: `owned_or_copied`
**Decision:** A value the test built is copied. A value the world already owns (by identity against the environment's bot) passes through. `send` fields and `edit` changes both use this rule.
**Why:** A copied module-level `MENU` keyboard stays equal to its unbound twin. A stored message passed as `reply_to_message` keeps aliasing the original, so later edits show through. Two triggers must not treat the same line differently.
**Code:** `aiogram/test/mounting.py` `owned_or_copied`; callers in `aiogram/test/actors.py` and `aiogram/test/world.py`. **Source:** 2026-08-25-apply-wave-2-field-feedback

### TW-10 A chat's messages are sorted on insert
**Decision:** `ChatState.add_message` scans back from the end and inserts by `message_id`.
**Why:** Tests write `chat.messages[-1]` for "newest". A message carried in from another environment has a foreign id, and appending it would break that.
**Rejected:**
- Sorting on read: `messages` is a plain list tests index and slice, and re-sorting each access costs and misleads.
- Renumbering a carried message: the id is how a test correlates what it fed with what the world holds.
**Code:** `aiogram/test/world.py` `ChatState.add_message`. **Source:** 2026-08-25-apply-wave-2-field-feedback

### TW-11 `world.chats` is guarded on assignment
**Decision:** `World.__setattr__` converts any mapping assigned to `chats` into a `ChatRegistry`. There is no `__post_init__` for it.
**Why:** The registry gives each chat its way back to the world, which binds stored messages to the bot. A guarantee set once at construction would be lost on `world.chats = {...}`.
**Code:** `aiogram/test/world.py` `World.__setattr__`, `ChatRegistry`. **Source:** 2026-08-25-apply-wave-2-field-feedback

## Result synthesis and the record-only boundary

### TW-12 Synthesize from pydantic field metadata, cached per type
**Decision:** Required fields get values by kind: ints from a counter, strings from the field name, nested models recursively, unions resolved to a member. Optional fields stay unset. Field lookups and per-return-type results are cached with `functools.cache`. Known-entity fields are seeded from the context: `chat` gets the world's chat and `from_user`/`user` its user, so results read as part of the environment.
**Why:** The walk derives from generated metadata, so no per-method table needs upkeep. Going through pydantic, not `typing` internals, keeps it stable across Python versions and PyPy.
**Code:** `aiogram/test/synthesis.py` `synthesize`, `synthesize_result`, `_required_fields`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-13 Accept odd but schema-valid results; fail loudly on shapes the walker cannot fill
**Decision:** A synthesized object may be semantically odd. A type the walker cannot build raises `SynthesisError`.
**Why:** Tests that care write an override; tests that don't keep passing. A loud error naming the type is better than a broken object.
**Code:** `aiogram/test/synthesis.py` `SynthesisError`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-14 `RECORD_ONLY` is guarded against overlap, not for completeness
**Decision:** A test asserts `RECORD_ONLY & set(REGISTRY)` is empty. It does not assert that every unmodeled method is listed. The list sits beside `REGISTRY`, grouped by reason, so a contributor adding a handler sees it, and one reason answers many questions. Clusters that are only deferred (stories, business account profile) are left out: "not yet" is not "no".
**Why:** Exhaustiveness would break the build on every Bot API bump for a list that is documentation. The overlap check catches the real failure: someone models a method that was a considered exclusion.
**Code:** `aiogram/test/modeling.py` `RECORD_ONLY`, `REGISTRY`. **Source:** 2026-08-23-specify-record-only-boundary

### TW-15 Seeded answers for calls with nothing to mutate
**Decision:** `sendChatAction`, `getFile`, `createInvoiceLink` and `getUserPersonalChatMessages` get a world-derived answer but store no state. `sendChatAction` still checks the chat exists.
**Why:** The line is "is there something to mutate". A chat action has no persistence in Telegram either.
**Code:** `aiogram/test/modeling.py` `handle_send_chat_action`, `handle_get_file`, `handle_create_invoice_link`, `handle_get_user_personal_chat_messages`. **Source:** 2026-08-20-complete-message-method-modeling

## Actors and triggers

### TW-16 Actors are bindings, not state
**Decision:** `user.in_(chat)` returns a light actor bound to `(user, chat)`. Triggers build an `Update`, await `dispatcher.feed_update`, and return the handler's result.
**Why:** The binding is a value, so actors are cheap and cannot drift. Returning the handler result keeps the `feed_raw_update` assertion style.
**Code:** `aiogram/test/actors.py` `UserActor`, `UserActor.in_`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-17 `click()` presses the button the bot actually sent
**Decision:** Callback triggers resolve the button from a stored message's real `reply_markup`.
**Why:** A renamed `callback_data` fails the test, instead of a hand-copied string reaching a handler nobody can reach.
**Code:** `aiogram/test/actors.py` `UserActor.click`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-18 A guard test keeps every `Update` variant reachable
**Decision:** A parametrized test walks `Update.model_fields` and asserts each variant has a trigger. There is no exemption set.
**Why:** A new Bot API variant then fails aiogram's CI with its name, instead of silently going untestable.
**Code:** `tests/test_testing/test_triggers.py` `TestEveryUpdateKindIsReachable`; triggers in `aiogram/test/actors.py`. **Source:** 2026-08-20-complete-actor-triggers

### TW-19 Outstanding queries live in a registry on the world
**Decision:** A trigger that issues a query registers its id in `World.pending_queries`. The answer handler pops it and raises `QUERY_TOO_OLD` when absent.
**Why:** Popping makes "already answered" and "never issued" one code path, as Telegram reports them. The registry is state with a lifetime, so it belongs to the per-test world.
**Rejected:**
- Validating in `CallbackQuery` construction or in the session: the state belongs to the world that `build()` isolates.
**Code:** `aiogram/test/world.py` `World.next_query_id`, `World.answer_query`; `aiogram/test/rejections.py` `QUERY_TOO_OLD`. **Source:** 2026-08-20-complete-actor-triggers

### TW-20 Channel posts route by chat type
**Decision:** `send()` in a channel produces `channel_post`; editing a stored post produces `edited_channel_post`.
**Why:** It keeps the actor API small and matches how the framework itself decides: by the chat the event belongs to.
**Code:** `aiogram/test/actors.py` `UserActor.send`, `UserActor.edit`. **Source:** 2026-08-20-complete-actor-triggers

### TW-21 Join requests are state; boosts are not
**Decision:** `ChatState.join_requests` holds pending requesters, and approving one makes them a member. `boost()` produces `chat_boost` and stores nothing.
**Why:** State exists only when an assertion needs it. Approval has a visible consequence; a boost has none without a boost model.
**Code:** `aiogram/test/world.py` `ChatState.join_requests`; `aiogram/test/actors.py` `request_join`, `boost`. **Source:** 2026-08-20-complete-actor-triggers

### TW-22 Payment triggers are independent steps
**Decision:** `shipping_query()`, `pre_checkout_query()` and `pay()` are separate triggers. None requires a predecessor.
**Why:** A payment test needs to assert the intermediate states. Real bots with digital goods skip the shipping step.
**Rejected:**
- One `complete_payment()`: it hides the intermediate states and forces an order real bots do not follow.
**Code:** `aiogram/test/actors.py` `shipping_query`, `pre_checkout_query`, `pay`. **Source:** 2026-08-20-complete-actor-triggers

### TW-23 Trigger signatures follow the actors, not the Bot API
**Decision:** Each trigger takes the few arguments a test varies and fills the rest from the binding and the world. `**data` is forwarded to `feed_update` on every trigger.
**Why:** Contextual dependency injection works the same way on every trigger.
**Code:** `aiogram/test/actors.py` `UserActor` triggers. **Source:** 2026-08-20-complete-actor-triggers

### TW-24 The actor binding decides the update kind
**Decision:** `in_(chat, topic=...)` and `in_(chat, business=...)` return new bound actors. The binding decides whether `send()` produces a plain, topic-tagged, or business message.
**Why:** Separate `send_business()`/`send_in_topic()` methods would multiply the trigger surface by every binding dimension.
**Code:** `aiogram/test/actors.py` `UserActor.in_`. **Source:** 2026-08-20-extend-testing-toolkit-api-surface

### TW-25 Chat-level events are triggered by the actor who caused them
**Decision:** Community service messages and business-connection enable/disable go through the actor (`add_chat_to_community`, `disable_business_connection`). Forum service messages are side effects of the modeled forum methods, not triggers.
**Why:** `event_from_user` then resolves like any other trigger. In production only the API emits forum service messages.
**Code:** `aiogram/test/actors.py` `UserActor`. **Source:** 2026-08-20-extend-testing-toolkit-api-surface

### TW-26 `state()` takes topic and business connection as keyword-only arguments
**Decision:** `env.state(user, chat=None, *, topic=None, business_connection=None)` passes `thread_id` and `business_connection_id` to `resolve_context`. A bound `actor.state()` fills them from the binding.
**Why:** The FSM key then matches what the dispatcher used under every strategy. Keyword-only keeps existing calls valid.
**Code:** `aiogram/test/environment.py` `BotTestEnvironment.state`; `aiogram/test/actors.py` `UserActor.state`. **Source:** 2026-08-20-extend-testing-toolkit-api-surface

## Message modeling

### TW-27 New send methods join `MEDIA_FIELDS` instead of getting handlers
**Decision:** `SendGame`, `SendPaidMedia`, `SendChecklist`, `SendLivePhoto`, `SendInvoice` and `SendRichMessage` map to the `Message` field their payload lands in and reuse the shared send handler.
**Why:** They inherit reply resolution, topic threading, business attribution and default resolution, and stay correct when those change.
**Rejected:**
- One handler per method: six near-copies that drift the first time `build_message` changes.
**Code:** `aiogram/test/modeling.py` `MEDIA_FIELDS`. **Source:** 2026-08-20-complete-message-method-modeling

### TW-28 `editMessageMedia` derives the field from the `InputMedia*` name
**Decision:** `InputMedia<Stem>` maps to the snake-cased `Message` field `<stem>`, derived from the method's media union.
**Why:** A future union member works with no change. A parametrized test over every member catches a name that does not map.
**Code:** `aiogram/test/modeling.py` `EDITABLE_MEDIA_FIELDS`. **Source:** 2026-08-20-complete-message-method-modeling

### TW-29 A stored message carries the scalars the request stated
**Decision:** After synthesizing the payload, request fields with the same name overwrite it, when `annotation_accepts` says the types fit.
**Why:** `sendLocation(latitude=48.85)` must store 48.85. Otherwise send and edit disagree. The type check skips same-named fields of different types (`sendVideo.cover` vs `Video.cover`).
**Code:** `aiogram/test/modeling.py` send path; `aiogram/test/synthesis.py` `annotation_accepts`. **Source:** 2026-08-20-complete-message-method-modeling

### TW-30 Batch forward/copy skip what they cannot move
**Decision:** `forwardMessages`/`copyMessages` share the per-message helpers of the single forms. Missing or unmovable ids are skipped; the returned id list shows what moved.
**Why:** Telegram skips rather than failing the batch. The returned list is the assertion surface.
**Code:** `aiogram/test/modeling.py` `handle_forward_many`, `handle_copy_many`, `forward_one`, `copy_one`. **Source:** 2026-08-20-complete-message-method-modeling

### TW-31 A forward records its origin; a copy clears it
**Decision:** A forward stores `forward_origin`: `MessageOriginChannel` from a channel, `MessageOriginChat` for a message sent on behalf of a chat, else `MessageOriginUser`. A forward of a forward keeps the first origin. Copies set `forward_origin=None`.
**Why:** The origin is the whole visible difference between a forward and a copy. The logic sits in the shared path, so batch forms get it too.
**Code:** `aiogram/test/modeling.py` `forward_origin`, `forward_one`, `copy_one`. **Source:** 2026-08-20-complete-message-method-modeling

### TW-32 `stopMessageLiveLocation` returns the stored message with `live_period` cleared
**Decision:** The handler clears `live_period` on the stored location and returns the stored message.
**Why:** A test can tell stopped from running, and a later live-location edit is refused as in Telegram.
**Code:** `aiogram/test/modeling.py` `handle_stop_live_location`. **Source:** 2026-08-20-complete-message-method-modeling

## Forum topics, business connections, communities

### TW-33 Topics are a registry on the chat; messages stay in one list
**Decision:** `ChatState.topics` holds `TopicState`. `TopicState.messages` is a filtered view over `ChatState.messages` by `message_thread_id`.
**Why:** Two parallel lists would need every edit, delete, forward and pin to update both. A view cannot drift.
**Code:** `aiogram/test/world.py` `ChatState.topics`, `TopicState.messages`. **Source:** 2026-08-20-extend-testing-toolkit-api-surface

### TW-34 A topic's thread id is its creation service message id
**Decision:** Creating a topic allocates a message id, emits `forum_topic_created`, and uses that id as `message_thread_id`. Blueprint topics go through the same path. General is a `TopicState` flagged `is_general`; its messages carry no `message_thread_id`, as in Telegram.
**Why:** That is how Telegram numbers topics, and a declared world then looks like one built by API calls.
**Code:** `aiogram/test/world.py` `create_topic`; `aiogram/test/blueprint.py` `Blueprint.build`; `aiogram/test/world.py` `TopicState.is_general`. **Source:** 2026-08-20-extend-testing-toolkit-api-surface

### TW-35 Posting into an unknown topic fails
**Decision:** A `message_thread_id` the forum does not have is refused with the API's thread-not-found rejection.
**Why:** A typo'd thread id must not produce a green test.
**Code:** `aiogram/test/rejections.py` `MESSAGE_THREAD_NOT_FOUND`; `aiogram/test/modeling.py` `landing`. **Source:** 2026-08-20-extend-testing-toolkit-api-surface

### TW-36 Business connections are world state keyed by connection id
**Decision:** `World.business_connections` holds owner, `user_chat_id`, `is_enabled`, `can_reply` and rights. `getBusinessConnection` reads it; an unknown id fails.
**Why:** Synthesizing a connection no test declared would hide setup errors.
**Code:** `aiogram/test/world.py` `World.business_connections`, `BusinessConnectionState`. **Source:** 2026-08-20-extend-testing-toolkit-api-surface

### TW-37 A business send is attributed to the account owner
**Decision:** When a send carries a known `business_connection_id`, the stored message is from the owner and `sender_business_bot` is the bot.
**Why:** `chat.messages[-1].from_user` then means what the customer sees.
**Code:** `aiogram/test/modeling.py` `build_message`, `_on_behalf_of`. **Source:** 2026-08-20-extend-testing-toolkit-api-surface

### TW-38 Two topic lookups: one for tests, one for calls
**Decision:** `ChatState.topic()` raises `WorldLookupError` listing the chat's topics. `topic_for_call()` answers `message thread not found`, or `TOPIC_DELETED` for an id in `deleted_topic_ids` (filled by `deleteForumTopic`).
**Why:** A test's unknown id is a setup gap; a bot's is Telegram's refusal.
**Code:** `aiogram/test/world.py` `ChatState.topic`, `topic_for_call`, `deleted_topic_ids` · **Source:** 2026-10-16-model-forum-topics-and-bot-rights

### TW-39 One function decides where the bot's message lands
**Decision:** `posting_topic()` is called from `build_message` and the copy/forward path. It resolves the thread and refuses a closed (or closed/hidden General) topic with `TOPIC_CLOSED` unless the bot created it or may manage topics.
**Why:** Every stored message with a thread goes through one rule.
**Code:** `aiogram/test/modeling.py` `posting_topic`, `build_message`, `landing` · **Source:** 2026-10-16-model-forum-topics-and-bot-rights

### TW-40 A topic message replies to the root unless it replies within the chat
**Decision:** `TopicState.root_reply()` sets the root as `reply_to_message` unless the message already replies to a message of its chat; an `external_reply` also gets the root. Applied in `build_message`, copy/forward, `service_message` and the actor's builder before `fields`.
**Why:** The Bot API server falls back to the root. An explicit actor reply wins.
**Code:** `aiogram/test/world.py` `TopicState.root_reply` · **Source:** 2026-10-16-model-forum-topics-and-bot-rights

### TW-41 Turning topics off keeps them
**Decision:** `UserActor.set_topics(enabled)` flips `is_forum` only, owner only, in a supergroup only. No update is fed. Forum methods go through `forum_chat()`, which refuses a non-forum. `createForumTopic` never turns a supergroup into a forum.
**Why:** TDLib's `toggle_channel_is_forum` checks the owner; neither TDLib nor the Bot API has a message for the switch.
**Code:** `aiogram/test/actors.py` `set_topics`; `aiogram/test/modeling.py` `forum_chat` · **Source:** 2026-10-16-model-forum-topics-and-bot-rights

### TW-42 User topic actions reuse the bot's code paths
**Decision:** `close_topic`, `reopen_topic`, `delete_topic` and the General-topic functions are plain functions shared by handlers and actor triggers; `service_message()` takes a `sender`. Deleting posts nothing; General close/reopen feed nothing. The actor must be creator of the topic, owner, or hold `can_manage_topics`; creating also accepts the chat permission (`may_create_topics`).
**Why:** One code path keeps tagging and root replies the same. There is no type for a deleted topic, and the General service messages are undocumented.
**Code:** `aiogram/test/modeling.py` `close_topic`, `delete_topic`, `may_create_topics`; `aiogram/test/actors.py` `_managed_topic`, `_require_topic_manager` · **Source:** 2026-10-16-model-forum-topics-and-bot-rights

### TW-43 A declared topic names its creator; by default it has none
**Decision:** `add_topic(..., creator=...)` takes a spec, actor, id or `blueprint.bot`. `build` posts `forum_topic_created` from that user. With no creator, the topic is no one's and its root is posted by the bot.
**Why:** Defaulting to the bot would exempt it from `TOPIC_CLOSED` in every suite and turn refusal tests green for the wrong reason.
**Code:** `aiogram/test/blueprint.py` `add_topic`, `TopicSpec.creator_id`, `Blueprint.build` · **Source:** 2026-10-17-model-other-senders-topic-creators-and-lost-updates

## Chat administration and membership

### TW-44 `ChatState` grows only by fields a method writes or a blueprint declares
**Decision:** `ChatState` carries `description`, `permissions`, `photo` and `sticker_set_name`, read by `getChat`. Nothing else from `ChatFullInfo` is added without that reason.
**Why:** It stops the "while we're here" growth toward all of `ChatFullInfo`.
**Code:** `aiogram/test/world.py` `ChatState`. **Source:** 2026-08-20-model-chat-administration

### TW-45 Admin changes emit service messages through the shared helper
**Decision:** `setChatTitle` and `deleteChatPhoto` emit their service messages via `service_message`, which allocates an id and stores the message.
**Why:** Handlers that filter on those messages become testable. The message counts in the chat, as in Telegram.
**Code:** `aiogram/test/modeling.py` `service_message`, `handle_set_chat_title`, `handle_delete_chat_photo`. **Source:** 2026-08-20-model-chat-administration

### TW-46 Membership reads are derived, not stored
**Decision:** `getChatAdministrators` filters members by creator/administrator status. `getChatMemberCount` counts present members.
**Why:** No cache means the answer cannot drift from what ban/promote handlers maintain.
**Rejected:**
- A separate `administrators` list: two sources of truth for one fact.
**Code:** `aiogram/test/modeling.py` `handle_get_chat_administrators`, `handle_get_chat_member_count`. **Source:** 2026-08-20-model-chat-administration

### TW-47 `getChatAdministrators` puts the creator first and omits other bots
**Decision:** The list is sorted creator first, then by user id. Other bots are dropped unless `return_bots` is passed.
**Why:** Telegram returns the creator first, and tests index `[0]`. The bot filter is documented API behavior.
**Code:** `aiogram/test/modeling.py` `handle_get_chat_administrators`. **Source:** 2026-08-20-model-chat-administration

### TW-48 `custom_title` and `tag` are separate and status-checked
**Decision:** `custom_title` applies to owner/administrator, `tag` to member/restricted. Each method rejects the status it does not apply to.
**Why:** The generated `ChatMember` variants carry them separately. Writing the wrong one would vanish on conversion.
**Code:** `aiogram/test/world.py` `MemberState.custom_title`, `MemberState.tag`; `aiogram/test/modeling.py` `_annotated_member`. **Source:** 2026-08-20-model-chat-administration

### TW-49 Rights and permissions are stored on `MemberState`
**Decision:** `MemberState.rights` and `MemberState.permissions` default to `None`. `None` on an administrator reads as the chat type's ordinary admin rights. `None` on a restricted member means every permission denied.
**Why:** A bot branches on the right it reads. `getChatMember` must report what was granted, not invent it.
**Code:** `aiogram/test/world.py` `MemberState`. **Source:** 2026-08-25-declare-bot-status-and-member-rights

### TW-50 `promoteChatMember` stores the whole mask; nothing true is a demotion
**Decision:** Each promotion replaces the stored mask. A request in which no right is true demotes to a plain member. The mask comes from `ChatAdministratorRights.model_fields`, so `is_anonymous` counts. A demotion clears `custom_title` and keeps `tag`: a title belongs to the admin status, a tag to the membership.
**Why:** The Bot API sets the full mask on every call and documents demotion as all `False`. Reading only `can_*` names would treat `is_anonymous=True` as a demotion.
**Code:** `aiogram/test/modeling.py` `handle_promote`. **Source:** 2026-08-25-declare-bot-status-and-member-rights, 2026-08-25-apply-wave-2-field-feedback

### TW-51 Chat-type scoping happens on read
**Decision:** `as_chat_member` takes the chat type and applies `scoped_rights`. A right that cannot exist in that chat reads `None`; one that can reads a plain boolean, even if unstated.
**Why:** The chat type is known only on read. That matches the real API and what `if member.can_pin_messages:` relies on.
**Code:** `aiogram/test/world.py` `CHAT_TYPE_SCOPED_RIGHTS`, `scoped_rights`, `MemberState.as_chat_member`. **Source:** 2026-08-25-declare-bot-status-and-member-rights

### TW-52 `administrator_rights()` returns an unscoped mask
**Decision:** The factory is not scoped. Its default grants a moderator's rights minus `can_promote_members` and stories, on an all-`False` floor from `model_fields`.
**Why:** Scoping at declaration would make stating a right grant fewer rights than saying nothing. The default is defined in one place so it can be argued with there.
**Code:** `aiogram/test/world.py` `administrator_rights`, `_ORDINARY_ADMIN_RIGHTS`. **Source:** 2026-08-25-declare-bot-status-and-member-rights

### TW-53 `bot_status` and `members[bot]` together are an error
**Decision:** Passing both raises, even when `bot_status` is `MEMBER`.
**Why:** An explicit argument is a statement. Letting one silently win surfaces three failures later.
**Rejected:**
- Merging with `bot_status` as a default: it makes a contradiction look composable.
**Code:** `aiogram/test/blueprint.py` `Blueprint._add_group_like`. **Source:** 2026-08-25-declare-bot-status-and-member-rights

### TW-54 `set_member` declares what a member may do
**Decision:** `members=` says what a user is; `set_member(chat, user, rights=..., permissions=...)` says what they may do. `rights` implies administrator and `permissions` implies restricted; an explicit `status` wins. Both together raise.
**Why:** The common case stays a one-line mapping. `rights` and `permissions` belong to different variants, so no member has both.
**Code:** `aiogram/test/blueprint.py` `Blueprint.set_member`. **Source:** 2026-08-25-declare-bot-status-and-member-rights

### TW-55 One owner guard for ban, restrict and promote
**Decision:** `_not_the_owner` refuses all three for the chat owner with "can't remove chat owner".
**Why:** Telegram answers all three the same. A guard on promote alone could be bypassed by banning the owner first.
**Code:** `aiogram/test/modeling.py` `_not_the_owner`. **Source:** 2026-08-25-declare-bot-status-and-member-rights

### TW-56 Permission couplings are applied on the way in
**Decision:** `granted_permissions` applies the documented couplings unless `use_independent_chat_permissions=True`, then fills the field-level defaults (`can_react_to_messages`, `can_edit_tag`, `can_manage_topics`) always. It returns a `model_copy` of the request's object.
**Why:** The stored mask is what Telegram would report, for every reader at once. `model_copy` keeps extra fields from future Bot API versions.
**Code:** `aiogram/test/world.py` `granted_permissions`. **Source:** 2026-08-25-apply-wave-2-field-feedback

## Polls and reactions

### TW-57 Votes are the source of truth; counts are derived
**Decision:** `PollState.votes` maps voter to chosen options. Option counts and totals are computed in `as_poll`.
**Why:** An aggregate stored next to its source drifts the first time a path updates one and not the other.
**Rejected:**
- Incrementing counters per vote: wrong the first time a retraction is added.
**Code:** `aiogram/test/world.py` `PollState.votes`, `PollState.vote_count`, `PollState.as_poll`. **Source:** 2026-08-20-model-polls-and-reactions

### TW-58 Polls live in a world registry keyed by poll id
**Decision:** `World.polls` holds every poll. A deleted poll message leaves the poll registered.
**Why:** `poll_answer` carries only the poll id, so `vote()` must resolve from it alone, as a real handler does.
**Code:** `aiogram/test/world.py` `World.polls`, `World.poll`. **Source:** 2026-08-20-model-polls-and-reactions

### TW-59 Reactions are world state; `Message` has no reactions field
**Decision:** `ChatState.reactions` maps message to user to reactions. `reactions_for` reads it; `reaction_counts` aggregates on read. Trigger `old_reaction` is read before the change and `new_reaction` after.
**Why:** The Bot API has no `Message.reactions`; inventing one would let tests depend on a fake field.
**Code:** `aiogram/test/world.py` `ChatState.reactions`, `reactions_for`, `reaction_counts`; `aiogram/test/actors.py` `react`. **Source:** 2026-08-20-model-polls-and-reactions

### TW-60 The bot reacts like any user, and the three reaction methods differ
**Decision:** `setMessageReaction` writes under the bot's id on one message. `deleteMessageReaction` clears one named actor on one message. `deleteAllMessageReactions` clears one named actor across the whole chat.
**Why:** Replace semantics then fall out of the table. `deleteAllMessageReactions` has no `message_id`; reading it as "clear this message" would be wrong.
**Code:** `aiogram/test/modeling.py` `handle_set_message_reaction`, `handle_delete_message_reaction`, `handle_delete_all_message_reactions`. **Source:** 2026-08-20-model-polls-and-reactions

### TW-61 Voting in a closed or anonymous poll raises at the trigger
**Decision:** `vote()` raises `WorldLookupError` for a closed poll and for an anonymous one, pointing at `poll_update()` for the latter.
**Why:** Telegram never delivers such an answer. A silent no-op would pass while asserting nothing; raising in the test's own code points at the test.
**Code:** `aiogram/test/actors.py` `UserActor.vote`, `UserActor.poll_update`. **Source:** 2026-08-20-model-polls-and-reactions

## Invite links

### TW-62 Links are a list on the chat with `is_primary` on each link
**Decision:** `ChatState.invite_links` holds `InviteLinkState`, looked up by URL. "The primary link" is a filter on `is_primary` and not revoked. `Blueprint.add_invite_link` declares links that materialize exactly like created ones.
**Why:** One source of truth. A separate pointer could dangle after a revoke.
**Code:** `aiogram/test/world.py` `InviteLinkState`, `ChatState.invite_links`; `aiogram/test/blueprint.py` `Blueprint.add_invite_link`. **Source:** 2026-08-20-model-invite-links

### TW-63 URLs are deterministic and unique
**Decision:** Links are `https://t.me/+<n>` from the world counter.
**Why:** Correlation needs unique URLs; reproducibility forbids randomness. Docs show correlating by the returned URL, not a literal.
**Code:** `aiogram/test/modeling.py` invite-link URL helper. **Source:** 2026-08-20-model-invite-links

### TW-64 Edit and revoke return the stored link
**Decision:** Handlers mutate `InviteLinkState` and convert to `ChatInviteLink` on the way out.
**Why:** A `model_copy` of a synthesized link would satisfy the type and defeat correlation.
**Code:** `aiogram/test/world.py` `InviteLinkState`; `aiogram/test/modeling.py` invite-link handlers. **Source:** 2026-08-20-model-invite-links

### TW-65 The two documented primary-link behaviors are modeled
**Decision:** `exportChatInviteLink` revokes the current primary and adds a new one. Revoking the primary adds a replacement. One helper does both.
**Why:** Both are documented API behavior, not server policy. One helper keeps exactly one active primary.
**Code:** `aiogram/test/world.py` `ChatState.replace_primary_invite_link`. **Source:** 2026-08-20-model-invite-links

### TW-66 `subscription_period` must be 2592000
**Decision:** Any other value is rejected.
**Why:** The Bot API states it as a fixed constant. It catches a real mistake for one comparison.
**Code:** `aiogram/test/modeling.py` `SUBSCRIPTION_PERIOD`; `aiogram/test/rejections.py` `SUBSCRIPTION_PERIOD`. **Source:** 2026-08-20-model-invite-links

## Bot profile

### TW-67 One `BotProfileState` with a dict per field
**Decision:** Commands are keyed by scope plus language; name, description and short description by language; default admin rights by `for_channels`; menu buttons by chat id (`None` is the default). `scope_key` builds the command key from every field of the scope, so a future scope variant keys correctly; an omitted scope equals `BotCommandScopeDefault`.
**Why:** Each field keeps its own key shape, so getters do not guess.
**Rejected:**
- One `dict[str, Any]` keyed by method name: it collapses the key shapes.
**Code:** `aiogram/test/world.py` `BotProfileState`; `scope_key`. **Source:** 2026-08-20-model-bot-profile-settings

### TW-68 Commands use exact keys; localized texts and menu buttons fall back
**Decision:** `getMyCommands` returns what was set for that exact scope and language, else `[]`. Name, descriptions and menu button fall back to the default entry. An empty string removes the dedicated entry.
**Why:** The docs' scope fallback is about what users see, not what the getter returns. The localized texts do document a default-language fallback.
**Code:** `aiogram/test/world.py` `BotProfileState.localized`, `set_localized`; `aiogram/test/modeling.py` `handle_get_my_commands`, `handle_get_chat_menu_button`. **Source:** 2026-08-20-model-bot-profile-settings

### TW-69 Unset values return documented defaults, not synthesis
**Decision:** Unset returns `[]`, `""`, `MenuButtonDefault()` or all-`False` admin rights. An unset name returns the bot's `first_name`.
**Why:** A bot that checks "are commands registered?" must take the right branch with no setup.
**Code:** `aiogram/test/modeling.py` `handle_get_my_name`, `handle_get_chat_menu_button`. **Source:** 2026-08-20-model-bot-profile-settings

### TW-70 The blueprint declares an initial profile
**Decision:** `Blueprint.set_bot_commands` and `Blueprint.set_bot_profile` declare a configured bot. `build()` deep-copies it.
**Why:** A test can start from a configured bot with no new isolation machinery.
**Code:** `aiogram/test/blueprint.py` `Blueprint.set_bot_commands`, `Blueprint.set_bot_profile`. **Source:** 2026-08-20-model-bot-profile-settings

## Stars and gifts

### TW-71 The star balance is derived from transactions
**Decision:** `StarLedger.balance` is the opening balance plus the sum of transactions.
**Why:** A stored balance drifts the first time a path forgets to update it, and money is the worst place for that.
**Rejected:**
- An `int` balance mutated in place: wrong the first time a refund path forgets to decrement.
**Code:** `aiogram/test/world.py` `StarLedger`. **Source:** 2026-08-23-model-stars-and-gifts

### TW-72 `pay()` records the charge
**Decision:** `pay()` stores a `ChargeState` (id, payer, amount, subscription flag) and the `successful_payment` message carries its id. The charge carries `is_refunded` and `is_subscription_canceled`, so a double refund and an unknown charge fail the same way.
**Why:** A test refunds the id its handler received. No fabricated identifiers.
**Code:** `aiogram/test/actors.py` `UserActor.pay`; `aiogram/test/world.py` `ChargeState`; `aiogram/test/modeling.py` `handle_refund_star_payment`. **Source:** 2026-08-23-model-stars-and-gifts

### TW-73 Owned gifts are one mapping with the owner as a field
**Decision:** `World.owned_gifts` maps owned id to `OwnedGiftState(owner_id=...)`.
**Why:** Readers differ only by owner filter, and transfer is a field write, not a move.
**Code:** `aiogram/test/world.py` `OwnedGiftState`, `World.owned_gifts`. **Source:** 2026-08-23-model-stars-and-gifts

### TW-74 The gift catalogue is fixed, invented data
**Decision:** `getAvailableGifts` returns a small hard-coded catalogue with stable ids and costs. Ids are documented as fake.
**Why:** `gifts[0].id` is the first thing a gift test reads, and synthesis would make it vary.
**Code:** `aiogram/test/modeling.py` `GIFT_CATALOGUE`, `gift_catalogue`. **Source:** 2026-08-23-model-stars-and-gifts

### TW-75 Spending does not check affordability
**Decision:** A gift with an insufficient balance succeeds and drives the balance negative.
**Why:** A negative balance is visible to a test; a silent rejection is not. Tests wanting the rejection use an override. This is the decision most likely to be revisited.
**Code:** `aiogram/test/modeling.py` `_spend`. **Source:** 2026-08-23-model-stars-and-gifts

## Sticker sets

### TW-76 Sticker sets are keyed by name
**Decision:** `World.sticker_sets` maps name to `StickerSetState`.
**Why:** Every method in the cluster takes `name`, so "name taken" is a membership test.
**Code:** `aiogram/test/world.py` `World.sticker_sets`, `StickerSetState`. **Source:** 2026-08-23-model-sticker-sets

### TW-77 Stickers are stored as generated `Sticker` objects
**Decision:** `StickerSetState.stickers` is a `list[Sticker]`, with no parallel state class. `replaceStickerInSet` puts the new sticker at the old one's position, as Telegram documents.
**Why:** Nothing in the cluster edits a sticker. If attribute setters are ever modeled, revisit this.
**Code:** `aiogram/test/world.py` `StickerSetState.stickers`; `aiogram/test/modeling.py` `handle_replace_sticker_in_set`. **Source:** 2026-08-23-model-sticker-sets

### TW-78 Sticker uploads mint a stable id and register no content
**Decision:** `uploadStickerFile` mints an id and stores no bytes.
**Why:** A bot uploads a sticker to put it in a pack, not to download it. If that proves wrong, route it through the file registry.
**Code:** `aiogram/test/modeling.py` `handle_upload_sticker_file`. **Source:** 2026-08-23-model-sticker-sets

## Files and downloads

### TW-79 A download with no content raises
**Decision:** `stream_content` raises `NoFileContentError` when the world has no bytes for the id. The message names the file id, `blueprint.add_file(...)`, `BufferedInputFile` and `env.on(GetFile).returns(...)`.
**Why:** `b""` cannot be told apart from an empty file, which real bots handle. The empty branch would be the only one tests exercise.
**Rejected:**
- Yielding `b""` and documenting it: indistinguishable from a real answer.
**Code:** `aiogram/test/session.py` `FakeTelegramSession.stream_content`; `aiogram/test/errors.py` `NoFileContentError`. **Source:** 2026-08-23-fail-loudly-on-unmodeled-downloads

### TW-80 Content is keyed by `file_id`; `getFile` makes the path invertible
**Decision:** `World.files` maps `file_id` to bytes. `getFile` sets `file_path` to the `file_id`, and the session recovers it from the URL's last segment. `getFile` does not fail for an id with no content.
**Why:** `file_id` is what a handler holds. Bots often call `getFile` for size or path and never download.
**Code:** `aiogram/test/world.py` `World.files`; `aiogram/test/modeling.py` `handle_get_file`; `aiogram/test/session.py` `stream_content`. **Source:** 2026-08-23-fail-loudly-on-unmodeled-downloads

### TW-81 `BufferedInputFile` uploads register their bytes
**Decision:** A send with a `BufferedInputFile` stores its bytes under the minted `file_id`. `FSInputFile` and `URLInputFile` are never read.
**Why:** Upload-then-download needs no declaration. The fake does not touch disk or network.
**Code:** `aiogram/test/synthesis.py` `with_passed_file`. **Source:** 2026-08-23-fail-loudly-on-unmodeled-downloads

## Waiting

### TW-82 One polling core in its own module
**Decision:** `poll_until` lives in `waiting.py`. It checks once before sleeping and once after the deadline. Each sleep is clamped to the time left, so `timeout` never overshoots by an interval. A timeout raises `WaitTimeoutError`, a `TimeoutError` subclass, with a message built lazily by `describe_timeout`.
**Why:** Both the environment and the world use it, and `world` must not import `environment`. The extra checks make an already-true wait free and count a change landing on the deadline.
**Code:** `aiogram/test/waiting.py` `poll_until`; `aiogram/test/errors.py` `WaitTimeoutError`. **Source:** 2026-08-25-add-waiting-helpers

### TW-83 The predicate's truthy value is returned; awaitables are accepted
**Decision:** `wait_for` returns whatever truthy value the predicate produced. A predicate may return an awaitable, detected with `inspect.isawaitable`.
**Why:** One helper both tests and fetches, by the truthiness rule Python users know. Tests may wait on coroutines.
**Rejected:**
- Separate bool and value helpers: the same code twice.
**Code:** `aiogram/test/waiting.py` `poll_until`; `aiogram/test/environment.py` `BotTestEnvironment.wait_for`. **Source:** 2026-08-25-add-waiting-helpers

### TW-84 `wait_for_message` matches everything the chat holds; the highest id wins
**Decision:** The scan covers every stored message, not only ones after the call. Every match is evaluated and the highest `message_id` is returned.
**Why:** Waiting only for new messages races with a send that already happened. Highest id is Telegram's own meaning of "newest", even when list order is off.
**Code:** `aiogram/test/world.py` `newest_match`, `ChatState.wait_for_message`. **Source:** 2026-08-25-add-waiting-helpers, 2026-08-25-apply-wave-2-field-feedback

### TW-85 A raising predicate is "no match", and its errors appear in the timeout
**Decision:** Exceptions from the predicate are swallowed per message, kept for the latest pass, and reported by message id when the wait times out.
**Why:** `m.text.startswith(...)` blows up on service messages with `text=None`. Reporting keeps a buggy predicate visible.
**Code:** `aiogram/test/world.py` `newest_match`. **Source:** 2026-08-25-add-waiting-helpers

### TW-86 A topic wait reads a callable view
**Decision:** The topic form takes a callable that returns the current view.
**Why:** A list captured once is a snapshot that can never gain the awaited message. It also lets chat and topic waits share one implementation.
**Code:** `aiogram/test/world.py` `TopicState.wait_for_message`. **Source:** 2026-08-25-add-waiting-helpers

### TW-87 The default timeout lives on the world
**Decision:** `BotTestEnvironment(default_wait_timeout=...)` sets `World.default_wait_timeout`. Chats and topics read it as derived properties. The floor is `DEFAULT_WAIT_TIMEOUT` (5 s). The field is `compare=False`.
**Why:** A suite states it once. A chat added later is covered by construction. It is configuration, so equal worlds stay equal.
**Code:** `aiogram/test/world.py` `World.default_wait_timeout`; `aiogram/test/waiting.py` `DEFAULT_WAIT_TIMEOUT`; `aiogram/test/plugin.py` `bot_env_wait_timeout`. **Source:** 2026-08-25-apply-wave-2-field-feedback

### TW-88 `description` is the second positional parameter
**Decision:** `wait_for(predicate, description)` and `wait_for_message(predicate, description)`. `timeout` and `interval` stay keyword-only.
**Why:** For a lambda, the description is the only thing a timeout can say about what was awaited. Positional makes it cheap.
**Code:** `aiogram/test/environment.py` `wait_for`, `wait_for_message_in`; `aiogram/test/world.py` `wait_for_message`. **Source:** 2026-08-25-apply-wave-2-field-feedback

### TW-89 Wait failures reuse the chat's own rendering and matcher
**Decision:** `wait_for(watch=...)` appends each watched chat's `describe_messages()` to the timeout. `wait_for_message_in` uses `newest_match` per chat and names only the chats still missing a match.
**Why:** One rendering and one "newest match by id" rule keep messages consistent. A broadcast wait must say who did not get the message.
**Code:** `aiogram/test/environment.py` `wait_for`, `wait_for_message_in`; `aiogram/test/world.py` `newest_match`, `describe_messages` · **Source:** 2026-08-25-target-overrides-and-diagnose-routing

### TW-90 A user in the watch vocabulary stands for their private chat
**Decision:** `as_views` accepts `UserSpec`/`UserState` and resolves them through `BotTestEnvironment.chat`, opening the private chat if needed.
**Why:** What a test holds for a player is the `add_user` declaration. None of the accepted types is iterable, so a lone item cannot be confused with a list.
**Code:** `aiogram/test/environment.py` `as_views` · **Source:** 2026-08-25-review-wave-4-hardening

### TW-91 Plugin knobs are separate value fixtures
**Decision:** `bot_env` reads `bot_env_wait_timeout`, `bot_env_clock_start`, `bot_env_enforce_bot_rights`, `bot_env_rate_limits`, `bot_env_deliver_service_messages_from_bots`, `bot_env_perturb_rejection_descriptions` and `bot_env_assert_updates_handled`.
**Why:** A project overrides one fixture instead of rewriting `bot_env`, the same shape as `bot_blueprint`/`bot_dispatcher`.
**Code:** `aiogram/test/plugin.py` · **Source:** 2026-08-25-harden-wave-3-edges

## Deep links and link classification

### TW-92 Following a link replays `/start` through an ordinary actor
**Decision:** `follow_deep_link` ends with `UserActor(env, user).send("/start <payload>")`, or bare `/start` with no payload. The button must be real: an explicit URL must be on a visible message's button, as with `click()`.
**Why:** Filters, middlewares, FSM and the command parser see what they see in production. The Bot API has no deep-link update to invent.
**Code:** `aiogram/test/actors.py` `UserActor.follow_deep_link`; `_require_button_url`. **Source:** 2026-08-25-follow-deep-links

### TW-93 One table decides what every link kind does
**Decision:** `_LINK_KINDS` maps a kind to `_LinkKindPolicy` (followable, rejection, query key, `match_by`). The query lookup order is derived from it. Adding a kind is one row.
**Why:** Classification, the followable set and the rejection text are one row, not three things to keep in sync.
**Code:** `aiogram/test/actors.py` `_LINK_KINDS`, `_LinkKindPolicy`, `_QUERY_KIND_LOOKUP`. **Source:** 2026-08-25-follow-deep-links, 2026-08-25-classify-links-per-spec

### TW-94 Refuse by name; never downgrade to a plain `/start`
**Decision:** Only `start` is followable. Every other kind, including an undefined query (`unknown_query`), is refused with what a real client does instead.
**Why:** Downgrading makes more tests pass by testing a flow the bot does not have.
**Code:** `aiogram/test/actors.py` `_LINK_KINDS`, `_rejection_message`. **Source:** 2026-08-25-follow-deep-links

### TW-95 A non-empty `start` wins over every other query parameter
**Decision:** A `start` with a value is checked before the table. An empty `?start=` claims nothing and becomes bare `/start` only if nothing else matches. A bare `t.me/<username>` is `start` with no payload.
**Why:** A client reads the parameter it recognizes and ignores the rest. Mini App buttons carry both `start` and `startapp`.
**Code:** `aiogram/test/actors.py` `UserActor._parse_deep_link`. **Source:** 2026-08-25-apply-wave-2-field-feedback, 2026-08-25-follow-deep-links

### TW-96 The scan skips what it cannot follow and explains it
**Decision:** The scan walks messages newest first and takes the first followable link to this bot. Unfollowable links to this bot are kept as candidates and listed with reasons if nothing followable is found. Links to other bots are skipped.
**Why:** A keyboard mixing a Mini App button with a `start` link still works, and a failure says why each button was refused.
**Code:** `aiogram/test/actors.py` `_find_deep_link_url`, `_visible_messages`. **Source:** 2026-08-25-follow-deep-links

### TW-97 Kinds that address no bot are refused before any username compare
**Decision:** `match_by` says which slot names the bot: `username`, `payload` (for `attach`), or none. Kinds with none are refused for what they are.
**Why:** `t.me/+abc` has no bot in it. "deep-links to @+abc" would point at the wrong problem.
**Code:** `aiogram/test/actors.py` `_LinkKindPolicy.match_by`, `_addressed_bot`. **Source:** 2026-08-25-follow-deep-links, 2026-08-25-classify-links-per-spec

### TW-98 Every documented link format has its own kind, built by two constructors
**Decision:** Kinds follow https://core.telegram.org/api/links. `_bot_link` and `_foreign_link` build rows with consistent wording. The `invoice` and `boost` rejections name `pay()`/`pre_checkout_query()` and `boost()`, the only kinds with an exact toolkit counterpart.
**Why:** No format is absorbed into a wrong neighbor (an invoice `t.me/$slug` is not read as a username).
**Code:** `aiogram/test/actors.py` `_bot_link`, `_foreign_link`, `_LINK_KINDS`. **Source:** 2026-08-25-classify-links-per-spec

### TW-99 Path shapes are classified in a fixed order
**Decision:** `_path_deep_link` checks `+` first, then `$`, then reserved segments, then shapes with a second segment (story, message link, direct Mini App), else `extra_path`.
**Why:** The order resolves ambiguity correctly, and it covers every documented shape, not just the ones tests reached.
**Code:** `aiogram/test/actors.py` `_path_deep_link`, `_RESERVED_PATH_KINDS`. **Source:** 2026-08-25-classify-links-per-spec

### TW-100 Phone and invite links are told apart by an all-digit tail
**Decision:** `t.me/+<digits>` is `phone`; any other `+` tail is `invite`. `tg://resolve?phone=` mirrors it.
**Why:** That is how Telegram's own clients disambiguate.
**Code:** `aiogram/test/actors.py` `_PHONE_NUMBER`, `_path_deep_link`. **Source:** 2026-08-25-classify-links-per-spec

### TW-101 An unlisted `tg://` host is `service_path`
**Decision:** `_TG_HOST_KINDS` lists hosts worth telling apart. Any other host falls back to `service_path`.
**Why:** It never claims a Telegram link is not one, without enumerating every app screen.
**Code:** `aiogram/test/actors.py` `_TG_HOST_KINDS`, `UserActor._parse_deep_link`. **Source:** 2026-08-25-classify-links-per-spec

### TW-102 The `start` payload is validated last
**Decision:** `_require_valid_start_payload` (`[A-Za-z0-9_-]{1,64}`) runs only after the kind and username checks pass, for explicit and scanned links alike. `validate_payload=False` skips it.
**Why:** A wrong-kind link should be refused for that reason. The default stays strict so a badly built button is named; the escape hatch reproduces payloads production bots do receive.
**Code:** `aiogram/test/actors.py` `_require_valid_start_payload`, `_START_PAYLOAD`, `follow_deep_link`. **Source:** 2026-08-25-classify-links-per-spec

### TW-103 A user's own private chat opens on demand; nothing else does
**Decision:** `World.ensure_private_chat(user)` builds the chat from `private_chat_shape`. It is reached by a followed link, an unbound actor's `chat`, and `in_()` with the actor's own id.
**Why:** Any user can open a DM with a bot, so an undeclared one is not a claim of absence. Other undeclared chats still raise: the world cannot invent a group's shape.
**Code:** `aiogram/test/world.py` `World.ensure_private_chat`, `private_chat_shape`; `aiogram/test/actors.py` `UserActor.in_`, `UserActor.chat`. **Source:** 2026-08-25-follow-deep-links

### TW-104 A link kind names which slot carries its bot
**Decision:** `_LinkKindPolicy.match_by` is `_MATCH_USERNAME`, `_MATCH_PAYLOAD` (`attach` only) or `""`. `_addressed_bot` is the only reader, used by `follow_deep_link` and `_find_deep_link_url`. Phone links defer to `attach` in the query.
**Why:** `t.me/<chat>?attach=<bot>` puts the bot in the query. Two call sites with their own copy of the rule is how the bug shipped.
**Code:** `aiogram/test/actors.py` `_LinkKindPolicy`, `_addressed_bot` · **Source:** 2026-08-25-follow-links-multi-signal

### TW-105 Query precedence: non-empty `start`, then real formats, then companions
**Decision:** A `start` with a value short-circuits the table; an empty one falls through. `_QUERY_KIND_LOOKUP` is stably sorted so `_COMPANION_QUERY_KEYS` (`startapp`, `startattach`, `text`) come last.
**Why:** `?start=&startapp=y` opens the Mini App. The deciding property is "also another format's companion", which cuts across aliases and kinds.
**Rejected:**
- Aliases before kinds: fixes `?startapp=x&text=y` but breaks `?appname=shop&startapp=ref`.
**Code:** `aiogram/test/actors.py` `_COMPANION_QUERY_KEYS`, `_QUERY_KIND_LOOKUP`, `_parse_deep_link` · **Source:** 2026-08-25-follow-links-multi-signal

### TW-106 `t.me/s/<name>` is a reserved path segment
**Decision:** `_RESERVED_PATH_KINDS["s"] = "channel_preview"`, checked before the Mini App shape.
**Why:** `s` is excluded from usernames like `joinchat`; the story shape `/<name>/s/<n>` stays unaffected.
**Rejected:**
- A single-letter special case inside the Mini App branch.
**Code:** `aiogram/test/actors.py` `_RESERVED_PATH_KINDS` · **Source:** 2026-08-25-follow-links-multi-signal

### TW-107 `validate_payload=False` skips one check, not classification
**Decision:** `follow_deep_link` calls `_require_valid_start_payload` only when `validate_payload` is true, after classification and the `followable` check.
**Why:** The flag must never make a refused kind followable.
**Code:** `aiogram/test/actors.py` `follow_deep_link`, `_require_valid_start_payload` · **Source:** 2026-08-25-follow-links-multi-signal

## Errors: setup gaps vs Telegram rejections, and refusal codes

### TW-108 Modeled refusals are the framework's own exceptions
**Decision:** A modeled refusal goes through `BaseSession.check_response`, so it becomes `TelegramBadRequest`, `TelegramForbiddenError` and so on, with Telegram's wording where known.
**Why:** The error path under test is the production one.
**Code:** `aiogram/test/errors.py` `raise_api_error`, `ApiRejection`; `aiogram/test/environment.py` `BotTestEnvironment._refuse`. **Source:** 2026-08-20-add-bot-testing-toolkit

### TW-109 An undeclared chat on the outbound path is a setup error
**Decision:** `resolve_chat` raises `WorldLookupError` listing the chats the world has. It never opens a private chat on demand. A declared user without a DM gets a hint naming `add_private_chat`, `ensure_private_chat` and "have the user write first".
**Why:** "chat not found" as `TelegramBadRequest` would be caught by the bot's blocked-user branch, and the test would pass on the wrong path. A real bot cannot write first into a private chat. The message names `env.on(SendMessage).raises(...)` for tests that want the real branch.
**Code:** `aiogram/test/modeling.py` `resolve_chat`, `_undeclared_chat_message`; `aiogram/test/world.py` `WorldLookupError`. **Source:** 2026-08-25-apply-wave-2-field-feedback

### TW-110 Two error types; the rule is "would Telegram answer this?", not the module
**Decision:** `ApiRejection` is a refusal Telegram would send; `handle_call` turns it into the real exception through `check_response`. `WorldLookupError` is a setup gap (undeclared entity, unrecorded charge, unknown gift, an inline message the toolkit does not model). Nothing converts or catches `WorldLookupError`. Both types are raised from `world.py` and `modeling.py`. `ChatState.require_message` raises `ApiRejection`; `World.chat` raises `WorldLookupError`. "Chat not found" on `getChat` is a rejection; the test asking `world.chat()` is a setup gap. The rule is in the `modeling.py` module docstring.
**Why:** A setup gap dressed as `TelegramBadRequest` is swallowed by a well-written bot's `except`. The layer a check sits in says nothing about whether Telegram would answer it.
**Code:** `aiogram/test/errors.py` `ApiRejection`; `aiogram/test/world.py` `WorldLookupError`, `aiogram/test/modeling.py`; `aiogram/test/environment.py` `handle_call` · **Source:** 2026-08-25-split-setup-errors-from-api-rejections

### TW-111 `ApiRejection` is public and carries the text without the prefix
**Decision:** `ApiRejection` is exported from `aiogram.test`. Its message omits `Bad Request:`; the prefix is added on conversion.
**Why:** World accessors reached outside a call raise it directly. A raise outside a call must not carry a prefix that would then double.
**Rejected:**
- A third "outside a call" type: same refusal, different audience.
**Code:** `aiogram/test/errors.py` `ApiRejection`; `aiogram/test/__init__.py` · **Source:** 2026-08-25-split-setup-errors-from-api-rejections

### TW-112 A trigger that asks for an impossible world raises `WorldLookupError`
**Decision:** Actor-side guards (promoting the owner, managing topics without the right, an invalid anonymous binding, a bot doing what only a person does (clicks, inline mode, votes, payments, paid media, boosts, subscriptions, deep links), an ephemeral command outside a group) raise `WorldLookupError`, worded like the call path's refusal where one exists.
**Why:** A trigger arranges the world; it is not a Bot API call, so the fix is in the test. The Bot API gives a bot no method for the person-only actions.
**Code:** `aiogram/test/actors.py` `_guard_not_owner`, `_require_topic_manager`, `_require_anonymous`, `_refuse_bot` · **Source:** 2026-08-25-review-wave-4-hardening, 2026-10-17-address-testing-toolkit-review, 2026-10-17-model-other-senders-topic-creators-and-lost-updates

### TW-113 Every refusal text is declared once
**Decision:** `aiogram.test.rejections` holds one `Rejection` per text: description, `source` (Bot API server, TDLib, API docs, or `None`) and code. Sites raise `rejections.NAME(**fields)`. A test fails on an `ApiRejection` built from a literal.
**Why:** A text is shared by unrelated sites, and a site needs only the name.
**Rejected:**
- An enum or a table keyed by method: texts do not follow methods.
**Code:** `aiogram/test/rejections.py` `Rejection`, `_declare` · **Source:** 2026-10-17-guarantee-refusal-codes-not-texts

### TW-114 Texts are sourced, not guaranteed; the code is the contract
**Decision:** A sourced text is copied verbatim and dated by `SOURCES_CHECKED`; others are best-effort. `ApiRejection` and `raise_api_error` refuse a 429 without `retry_after` and `retry_after` with another code. The toolkit's own tests fail at teardown on a refusal whose exception type disagrees with its code.
**Why:** Telegram guarantees no text. A wrong code/retry pairing yields the wrong aiogram exception, and `aiogram.exceptions` carries no `error_code`, so the type is the observable part.
**Code:** `aiogram/test/rejections.py` `SOURCES_CHECKED`; `aiogram/test/errors.py` `ApiRejection.__init__`; `tests/test_testing/conftest.py` · **Source:** 2026-10-17-guarantee-refusal-codes-not-texts, 2026-10-14-add-controllable-world-time

### TW-115 A raised exception can be traced to its rejection, and texts can be perturbed
**Decision:** The environment maps each raised exception to its `ApiRejection` in a weak map, so `rejection_of()`/`rejection_fields()` work even with perturbed text; foreign exceptions are matched against the declared descriptions, which never overlap. `perturb_rejection_descriptions` swaps descriptions for a marker plus scrambled words, the same each run, keeping code, type and `retry_after`.
**Why:** Lets a test check a bot's fallback for text it does not recognise. A message the test declared itself is left alone.
**Code:** `aiogram/test/rejections.py` `remember`, `rejection_of`, `perturb`; `aiogram/test/environment.py` · **Source:** 2026-10-17-guarantee-refusal-codes-not-texts

## Object identity and binding (mounting)

### TW-116 Bind by walking the object graph and calling `as_()`, not by re-parsing
**Decision:** `bindables()` walks the tree iteratively and calls `BotContextController.as_(bot)` on each node. The objects stay the same objects.
**Why:** A dump/validate round-trip mints copies, which breaks the identity between a returned message and the stored one. A recursive walk hits the recursion limit on long reply chains.
**Rejected:**
- `model_dump()` + `model_validate(context=...)`: pydantic skips model instances, so it needs a real round-trip that copies, reshapes unions and fails on deep graphs.
**Code:** `aiogram/test/mounting.py` `bindables`, `mount` · **Source:** 2026-08-25-mount-results-to-bot

### TW-117 Bind on the way in, when a message is stored
**Decision:** Content is bound when it enters the world (`ChatRegistry.__setitem__`, `ChatState.add_message`). `World.bind(bot)` sweeps content stored before the bot existed, such as a declared topic's service message.
**Why:** Storage is the one moment every producer shares, so every stored message has working shortcuts with no per-producer rule.
**Code:** `aiogram/test/world.py` `World.bind`, `ChatRegistry.__setitem__` · **Source:** 2026-08-25-mount-results-to-bot

### TW-118 An object that already has an owner is left alone, and the walk stops there
**Decision:** `mount` binds only unbound nodes and prunes at bound ones. Ownership is compared by identity (`bound_elsewhere`), never with `==`.
**Why:** Re-binding to a second `Bot` on the same session would silently change which `DefaultBotProperties` later shortcuts use. `Bot.__eq__` compares token hashes, so two environments from one blueprint have equal bots.
**Code:** `aiogram/test/mounting.py` `mount`, `bound_elsewhere` · **Source:** 2026-08-25-mount-results-to-bot

### TW-119 A chat reads its bot off its world; the registry installs the backref
**Decision:** `ChatState.bound_bot` is derived from `self.world.bound_bot`. `ChatRegistry` sets `chat.world` in `__setitem__` and routes `update`, `setdefault` and `|=` through it.
**Why:** A copied `bound_bot` per chat missed chats added after the bind. `dict` implements those three methods in C without calling `__setitem__`.
**Rejected:**
- Storing `bound_bot` on each chat at bind time: chats added later stored unbound messages.
**Code:** `aiogram/test/world.py` `ChatRegistry`, `ChatState.bound_bot` · **Source:** 2026-08-25-mount-results-to-bot

### TW-120 Copy in once, at `handle_call`, after the call log records the caller's object
**Decision:** `handle_call` records the resolved call, then hands everything downstream a `detached_copy`. Handlers never copy.
**Why:** `env.calls` shows what the code under test built, and a rule that lives in one place cannot be forgotten by the next handler. The rule is stated in the `modeling.py` module docstring.
**Code:** `aiogram/test/environment.py` `BotTestEnvironment.handle_call` · **Source:** 2026-08-25-mount-results-to-bot

### TW-121 Messages are shared on the way out; values and override results are copied
**Decision:** A stored `Message` is returned as is, so `chat.messages[-1] is result`. `getChat`, `getMyCommands`, `getMyDefaultAdministratorRights` and `getChatMenuButton` return copies. Each call gets its own copy of the override's result, already bound to the caller.
**Why:** Message identity is what state assertions rely on. A value returned uncopied would be mounted to the bot and stop comparing equal to the test's declared constant. The declared object is often a module-level constant. Sharing it would let follow-up edits leak between calls and keep every `Bot` that received it alive.
**Code:** `aiogram/test/modeling.py` (those handlers); `aiogram/test/overrides.py` `Outcome.apply`, `fresh_result` · **Source:** 2026-08-25-mount-results-to-bot

### TW-122 `detached_copy` rebuilds models, mappings and lists, and shares every other leaf
**Decision:** The copy rebuilds pydantic models, mappings, lists and immutable containers. Dates, enums, sentinels and `InputFile`s are shared. The binding is decided while copying (`bot=`). `derive_message` shares the untouched subtree with the original and copies only the changes.
**Why:** `URLInputFile` holds a bot, so following leaves duplicates the bot, session, environment and world. A model's `_bot` is a private attribute the walk never follows. Detaching the whole derived copy unbound the original's children, so a stored message lost its shortcuts when something else was edited.
**Rejected:**
- `copy.deepcopy`: copies through leaves and fails around 200 levels deep.
**Code:** `aiogram/test/mounting.py` `detached_copy`, `owned_or_copied`; `aiogram/test/world.py` `derive_message` · **Source:** 2026-08-25-mount-results-to-bot

### TW-123 Updates are adopted before `feed_update`; a foreign update is copied
**Decision:** `adopt()` runs one `bindables` pass. Unbound nodes are claimed in place. If any node belongs to another bot, the whole update is copied for this environment. Carried messages are then registered in their chat.
**Why:** `feed_update` re-validates an update with a different bot through JSON, which breaks `received is chat.messages[-1]`. A module-level update fed to two environments would otherwise route replies into the first world. Registering keeps the chat's id allocator ahead.
**Code:** `aiogram/test/environment.py` `adopt`, `feed`, `_register_carried_message` · **Source:** 2026-08-25-mount-results-to-bot, 2026-10-17-address-testing-toolkit-review

### TW-124 The plugin explains an inequality that is only about binding
**Decision:** `pytest_assertrepr_compare` detects same type, same dump, different bot, and points at `model_dump()`. The dump is guarded by `except Exception`.
**Why:** The repr hides the bot, so the two sides print the same. The hook runs on every failing `==` in every project with aiogram, and it must never replace the user's real failure with its own traceback.
**Code:** `aiogram/test/plugin.py` `pytest_assertrepr_compare`, `_differ_only_in_binding` · **Source:** 2026-08-25-mount-results-to-bot

## World ownership and registration

### TW-125 Chat ownership is enforced per chat, in `ChatRegistry.__setitem__`
**Decision:** Registering a chat whose `.world` is another world raises `WorldLookupError`. A fresh chat (`world is None`) is adopted; a chat of this world is a no-op. The message lists three remedies, each with `chat.world = None`, and tests `exec` them.
**Why:** Wiring is a rewrite of `chat.world` on an object the donor still holds. Checking only on assignment missed `dict(other.chats)`, which goes in item by item.
**Rejected:**
- Auto-detach on `del`/`pop`: hides a `chat.world` mutation inside a removal.
- Hardening `update`/`setdefault`/`|=` separately: they already route through `__setitem__`.
**Code:** `aiogram/test/world.py` `ChatRegistry.__setitem__` · **Source:** 2026-08-25-review-wave-4-hardening

### TW-126 Assigning another world's live registry is refused; a plain mapping is converted
**Decision:** `World.__setattr__` refuses a `ChatRegistry` of another world and leaves both worlds unchanged. A plain mapping becomes a fresh `ChatRegistry(self)`. A registry of this world is left alone by identity.
**Why:** A registry holds the donor's own `ChatState` objects, so rewrapping silently moves them to the new world. `world.chats = {1: chat}` is the natural way to rebuild chats and needs wiring.
**Rejected:**
- Rewrapping the foreign registry: a quiet failure found only far downstream.
- Rewrapping with a warning: suites filter warnings.
- Copying the chats automatically: a guess about what the caller meant.
**Code:** `aiogram/test/world.py` `World.__setattr__` · **Source:** 2026-08-25-target-overrides-and-diagnose-routing, 2026-08-25-review-wave-4-hardening

### TW-127 Carried messages: equality decides a collision, an edit replaces
**Decision:** `_register_carried_message` raises `WorldLookupError` when a different message holds the same id. It compares after `feed` has bound the incoming message, so equal content with the same binding is a silent re-feed. `edited_message`, `edited_channel_post` and `edited_business_message` replace the stored version under their id.
**Why:** A dropped incoming message would make a later wait hang with no clue. Pydantic equality includes `_bot`. An edit is the new version of a message, not a second message colliding with it.
**Rejected:**
- Identity comparison: two copies of the same source message from two `feed()` calls are different objects.
**Code:** `aiogram/test/environment.py` `_register_carried_message` · **Source:** 2026-08-25-harden-wave-3-edges, 2026-10-14-align-actor-triggers-with-bot-api

### TW-128 A user's private chat opens on demand from every accessor
**Decision:** `env.chat(user_id)` opens a declared user's private chat, as `env.user(u).chat` does. `ensure_private_chat` takes a `UserState`, an `int` or anything with `.id`, by duck typing.
**Why:** The same chat must be reachable from both accessors. `world.py` cannot import `UserSpec` at module scope without a cycle.
**Code:** `aiogram/test/environment.py` `chat`; `aiogram/test/world.py` `World.ensure_private_chat` · **Source:** 2026-08-25-target-overrides-and-diagnose-routing, 2026-08-25-harden-wave-3-edges

### TW-129 Runtime additions reuse the blueprint's builders on a scratch blueprint
**Decision:** `env.add_*` declare on a scratch `Blueprint` for the same bot and turn the declaration into state with `chat_state()`/`user_state()`. Ids skip what the world has taken. Members are named by spec, actor or id. The environment's own blueprint is never written to.
**Why:** Defaults, bot membership and permissions then match a declared world. The blueprint is shared by tests at any scope.
**Code:** `aiogram/test/environment.py` `add_user`, `add_group`, `_scratch`; `aiogram/test/blueprint.py` `chat_state`, `user_state` · **Source:** 2026-10-17-finish-tasks-record-routes-parse-markup

## Overrides and targeting

### TW-130 Override filters match the resolved call; unknown fields fail at declaration
**Decision:** `env.on(Method, **fields)` stores field pairs on a frozen `MethodMatcher` and checks them after `resolve_defaults`. `.where(predicate)` adds a callable. An unknown field raises `TypeError`.
**Why:** The real API sees resolved defaults. A typo'd filter that never fires is the worst silent failure.
**Rejected:**
- Matching the call as the handler built it: a filter's truth would depend on whether a field was stated.
**Code:** `aiogram/test/overrides.py` `MethodMatcher`, `OverrideBuilder.where`, `_validated_fields` · **Source:** 2026-08-25-target-overrides-and-diagnose-routing

### TW-131 A rule that does not match is not consumed
**Decision:** `OverrideRegistry.take` walks rules in registration order. A rule that rejects the call keeps its `times` budget.
**Why:** Two `times=1` rules for two chats stay independent of the order the bot messages them in.
**Code:** `aiogram/test/overrides.py` `OverrideRegistry.take` · **Source:** 2026-08-25-target-overrides-and-diagnose-routing

### TW-132 The call is recorded before overrides are consulted
**Decision:** A call answered by an override, including a raising one, is in `env.calls`.
**Why:** A test asserts separately that the bot tried the right chat and that it coped with the refusal.
**Code:** `aiogram/test/environment.py` `handle_call` · **Source:** 2026-08-25-target-overrides-and-diagnose-routing

### TW-133 Chat-addressing fields compare after resolving both sides through the world
**Decision:** For `ADDRESSING_FIELDS` (`chat_id`, `from_chat_id`, `sender_chat_id`) the matcher tries equality, then resolves both values with `resolve_addressing`. Every other field is exact.
**Why:** A bot that addresses `@alice` and a test that names id 1 must match, in both directions.
**Code:** `aiogram/test/overrides.py` `ADDRESSING_FIELDS`, `MethodMatcher.matches`; `aiogram/test/environment.py` `resolve_addressing` · **Source:** 2026-08-25-review-wave-4-hardening

### TW-134 `fired` counts matches; only expected rules are reported as unfired
**Decision:** `OverrideRule.fired` grows in `take`. `unfired()` lists rules with `expected=True` and `fired == 0`. `block_chat` registers its rules with `expected=False`. `assert_overrides_consumed()` is opt-in, and wait timeouts reuse `describe_unfired()`.
**Why:** A block is one simulation spelled as forty alternatives, not forty predictions. A test may declare a rule for a path it proves is never taken.
**Rejected:**
- Per-handle accounting: hides a hand-written handle where only one rule matched.
- Automatic check at teardown: breaks "prove the bot never went there".
**Code:** `aiogram/test/overrides.py` `OverrideRule`, `OverrideRegistry.unfired`, `describe_unfired` · **Source:** 2026-08-25-review-wave-4-hardening

### TW-135 A block covers delivery plus a reviewed list of in-chat actions
**Decision:** `BLOCKED_METHODS` is `DELIVERY_METHODS` (by `Send`/`Copy`/`Forward` prefix) plus edits, live-location stop, `stopPoll`, the reaction family and pin/unpin. `deleteMessage(s)` and the ephemeral edit/delete family are documented exclusions. A new `Edit*`/`Stop*`/`Pin*`/reaction method needs a row or an exclusion line.
**Why:** A blocked user's recovery path (edit, unpin, clear reaction) must fail as in production. Deletion limits are about age and rights, and a wrong 403 fails a cleanup path that works in production.
**Code:** `aiogram/test/overrides.py` `BLOCKED_METHODS`, `_BLOCKED_EXTRA_METHOD_NAMES` · **Source:** 2026-08-25-review-wave-4-hardening

### TW-136 A block is one rule per method per addressing field; `user_id` only on delivery
**Decision:** `block_chat` registers a `chat_id` rule for every blocked method and a `user_id` rule only on delivery methods. The rules have no `times` budget.
**Why:** `sendGift` addresses by `user_id` only. On `deleteMessageReaction`, `user_id` is a participant, not the addressee. A budget would un-block the user on call n+1.
**Rejected:**
- One predicate for "chat_id or user_id": a predicate cannot describe itself for failure messages.
**Code:** `aiogram/test/overrides.py` `block_chat` · **Source:** 2026-08-25-review-wave-4-hardening, 2026-08-25-target-overrides-and-diagnose-routing

### TW-137 `raises()` checks what it is given at declaration
**Decision:** `require_raisable()` reads the exception's constructor with `inspect.signature` and refuses a class that needs more than `method` and `message`, showing an instance to pass instead. `env.blocked()` is not checked.
**Why:** `TelegramRetryAfter` and `TelegramMigrateToChat` built from the class failed with `TypeError` inside the bot's call, far from the declaration.
**Code:** `aiogram/test/overrides.py` `require_raisable` · **Source:** 2026-10-17-finish-tasks-record-routes-parse-markup

## Routing diagnostics

### TW-138 A route record is opened inside aiogram's error middleware
**Decision:** An outer update middleware opens a `RouteRecord`. An inner middleware on every other observer fills in the handler, module and router. `handled` follows the dispatcher's `UNHANDLED`; `handler` is a separate field.
**Why:** Inside the error middleware the record sees exceptions the bot's error handler swallows. "Handled" and "a handler ran" are different questions, and a middleware can swallow an update.
**Code:** `aiogram/test/environment.py` `_RouteMiddleware`, `_HandlerMiddleware`, `RouteRecord` · **Source:** 2026-08-25-target-overrides-and-diagnose-routing

### TW-139 The record in flight lives in a module-level `ContextVar`
**Decision:** `_ROUTE_IN_FLIGHT` holds the innermost record of the current task. A nested feed shadows it and restores by token.
**Why:** Concurrent feeds run in their own tasks with their own context. A per-environment variable would break `copy.deepcopy(world)`, since a `ContextVar` cannot be copied.
**Code:** `aiogram/test/environment.py` `_ROUTE_IN_FLIGHT` · **Source:** 2026-08-25-review-wave-4-hardening

### TW-140 Diagnostics answer per trigger scope, held as a context-local frame
**Decision:** A `_TriggerFrame` (records, owning environment, `closed` flag) lives in `_TRIGGER_SCOPES`. `trigger()` and a bare `feed` push a frame unless this environment has one open in this context. Readers use the open frame, else the last completed one. A direct `feed_update` gets a one-record frame.
**Why:** A counter plus a list on the environment erased records under `gather`, absorbed unrelated feeds and leaked across environments. The `closed` flag stops a background task's copied context from appending to a finished trigger.
**Rejected:**
- Locking, or merging concurrent triggers: two `gather` branches are two things the test did.
**Code:** `aiogram/test/environment.py` `_TriggerFrame`, `_TRIGGER_SCOPES`, `trigger`, `routes` · **Source:** 2026-08-25-review-wave-4-hardening

### TW-141 `last_route` prefers the record that raised; `assert_handled_by` scans them all
**Decision:** Order: newest record with an exception, else newest handled, else newest of any kind. It matches `module.qualname` by substring across the whole scope. The failure lists every record with any captured exception.
**Why:** A raising handler leaves its record "not handled" while another update of the trigger is handled, so the docs' idiom would pass while the bot is broken. `member.join()` still reports the `chat_member` record. For a multi-update trigger, either update claiming the handler is correct behavior.
**Code:** `aiogram/test/environment.py` `last_route`, `assert_handled_by` · **Source:** 2026-08-25-review-wave-4-hardening

### TW-142 `SkipHandler` is control flow; `CancelHandler` is a failure
**Decision:** `_HandlerMiddleware` catches `SkipHandler`, clears handler, module and router, and re-raises without an exception. `CancelHandler` is recorded like any exception.
**Why:** aiogram's handler loop catches only `SkipHandler`, so a raised `CancelHandler` fails the update.
**Code:** `aiogram/test/environment.py` `_HandlerMiddleware` · **Source:** 2026-10-14-align-actor-triggers-with-bot-api

### TW-143 The history keeps frames, and the unhandled check reasons per trigger
**Decision:** Every frame is appended to the history; `all_routes` flattens it. `assert_updates_handled()` flags a whole frame when none of its records was handled, else only records that raised. `assert_unhandled()` marks the current frame as expected and fails if it has nothing to flag. The plugin runs the check from `pytest_runtest_call` when `bot_env_assert_updates_handled` is true.
**Why:** `member.join()` with an unclaimed service message must pass. Running in the call phase fails the test, not its teardown, and skips tests that already failed.
**Code:** `aiogram/test/environment.py` `all_routes`, `assert_updates_handled`, `assert_unhandled`; `aiogram/test/plugin.py` `pytest_runtest_call` · **Source:** 2026-10-17-finish-tasks-record-routes-parse-markup

## World time and clock

### TW-144 One world clock that starts at real time and stands still
**Decision:** `World.now` starts at the wall clock to the second, unless `clock_start`/`Blueprint.build(start=...)` is given. `next_date()` returns it; only `advance_time` moves it. Declared topics are dated at the start.
**Why:** Bots compute dates from the real clock. Nothing in the toolkit orders by date, and a ticking clock would make limits depend on unrelated updates.
**Rejected:**
- Fixed start at `BASE_DATE`: refused `close_date=datetime.now()+5min` and turned real `until_date`s into "forever".
- Keeping the tick plus a second "explicit" clock: two answers to "how old is this message".
**Code:** `aiogram/test/world.py` `wall_clock`, `World.now`; `aiogram/test/blueprint.py` `Blueprint.build` · **Source:** 2026-10-14-add-controllable-world-time

### TW-145 `advance_time` runs a due-event queue
**Decision:** It refuses negative steps (`ValueError`) and re-entry (`RuntimeError`). It pops due events in moment then scheduling order, moves the clock to each and runs it; new events before the target fire in the same call. Dispatches share one route scope; an advance that dispatches nothing keeps the previous routes. A raising handler leaves the clock at that moment. `env.schedule()` is public.
**Why:** Expiry stays deterministic between the test's own steps, with no background task.
**Code:** `aiogram/test/environment.py` `advance_time`, `schedule` · **Source:** 2026-10-14-add-controllable-world-time

### TW-146 Expiry is settled when a membership is read, with no update
**Decision:** `ChatState.member()` calls `MemberState.settle(now)`, which lifts an expired restriction or ban. Member counts use `present_members()` through the same accessor. Live locations, message age and query windows are compared with `now` at use. Settling changes state silently.
**Why:** Every reader goes through one accessor, so the bot and the test see the same status. The Bot API documents no such update; inventing one would create traffic a bot could depend on in tests only.
**Rejected:**
- A computed "effective" view: every reader would need the clock, and tests would disagree with the bot.
**Code:** `aiogram/test/world.py` `MemberState.settle`, `ChatState.member`, `present_members` · **Source:** 2026-10-14-add-controllable-world-time

### TW-147 Dates are resolved, then `until_date` is normalized
**Decision:** `resolve_date` turns a `timedelta`, a Unix `int` or a naive `datetime` into an aware moment in whole seconds. `normalize_until` applies "under 30 s or over 366 days is forever" and returns `None` for forever. Invite-link dates are never turned into forever.
**Why:** It mirrors aiogram's serializer and the Bot API rule, and keeps one rule out of unrelated dates.
**Code:** `aiogram/test/modeling.py` `resolve_date`, `normalize_until` · **Source:** 2026-10-14-add-controllable-world-time

### TW-148 Polls schedule their own close
**Decision:** `sendPoll` refuses `open_period` with `close_date`, stores the close moment on the `PollState` and schedules a close. On fire, an open poll closes through the `stopPoll` code and a `poll` update is fed; a stopped poll is skipped.
**Why:** Scheduled poll closing is the one timed event that produces an update.
**Code:** `aiogram/test/modeling.py` `handle_send_poll`, `_close_poll` · **Source:** 2026-10-14-add-controllable-world-time

### TW-149 Answer windows exist only where the Bot API documents them
**Decision:** `ANSWER_WINDOWS` holds only the 10-second pre-checkout limit, measured from `World.query_issued`. A reply to an ephemeral command must come within 15 seconds of its `date`.
**Why:** Other windows are undocumented.
**Code:** `aiogram/test/world.py` `ANSWER_WINDOWS`, `query_issued`; `aiogram/test/modeling.py` `_EPHEMERAL_REPLY_WINDOW` · **Source:** 2026-10-14-add-controllable-world-time

### TW-150 The host clock is not patched; fast sleeps are a recipe
**Decision:** The toolkit never freezes `datetime.now`, `time.time` or `loop.time`. The docs point to `time-machine` and `looptime`, and show a recipe that swaps the app's own pause helper. `test_sleep_scaling_recipe.py` runs the recipe from `testing.rst`.
**Why:** asyncio cannot tell a bot's timers from a driver's. Large `looptime` jumps can exhaust a driver's own deadlines.
**Rejected:**
- A time-control mode: needs a timer-ownership rule that does not exist.
**Code:** docs only · **Source:** 2026-10-17-finish-tasks-record-routes-parse-markup, 2026-08-25-harden-wave-3-edges

## Bot API fidelity

### TW-151 Click targets are re-resolved against the stored message
**Decision:** `click(message=m)` looks `m` up by id in the actor's chat or its ephemeral messages and needs the button on the stored version. An explicit message must be visible to the actor.
**Why:** The stored version is the one dispatched; Telegram would not deliver a press on a button that does not exist.
**Code:** `aiogram/test/actors.py` `click`, `_require_visible` · **Source:** 2026-10-14-align-actor-triggers-with-bot-api

### TW-152 Guest query ids come from the query counter; answering is record-only
**Decision:** A guest query id comes from `world.next_query_id()` with no kind, so it is not tracked as pending. `answerGuestQuery` stays in `RECORD_ONLY`.
**Why:** The recorded call is the whole useful assertion for mini-app handoffs.
**Code:** `aiogram/test/actors.py` `guest_message`; `aiogram/test/modeling.py` `RECORD_ONLY` · **Source:** 2026-10-14-align-actor-triggers-with-bot-api

### TW-153 Synthesized values follow the Bot API by reflection
**Decision:** A `str` field `f` on model `M` takes the first member of `aiogram.enums.<M><F>`. Booleans are `False`. List counts (`total_count`, `voter_count`, `total_voter_count`, `pending_update_count`) are `0`. File ids are `file-<n>`/`unique-<n>` from a world counter, and a `str` media input is kept as the `file_id`. Dice values fold into each emoji's range.
**Why:** butcher names enums this way, so a Bot API bump needs no toolkit change. A count that disagrees with its empty list breaks `[0]` access.
**Code:** `aiogram/test/synthesis.py` `_enumerated`, `_LIST_COUNTS`; `aiogram/test/world.py` `last_file_number`; `aiogram/test/modeling.py` dice table · **Source:** 2026-10-14-align-fake-api-with-bot-api

### TW-154 A service message is one that carries no sendable content
**Decision:** `is_service_message` checks the message against the content fields sends produce (media fields, text, poll and the named kinds). Invoice, paid media, giveaway and giveaway-winner messages are named where the Bot API names them.
**Why:** No list of service fields to keep in sync.
**Code:** `aiogram/test/modeling.py` `is_service_message`, `_copyable` · **Source:** 2026-10-14-align-fake-api-with-bot-api

### TW-155 Declared state, star ledgers and business ids follow the API's own rules
**Decision:** `Blueprint.build` runs declared permissions through `granted_permissions`, creates topics through `create_topic`, and stores a declared poll as `sendPoll` does. `StarTransactionState.partner_id` is kept; `as_star_transaction` reports a positive amount and a `TransactionPartnerUser` as source or receiver. `allocate_message_id(connection)` gives a business message the next id after both the chat's and the connection's last one. Ids found in two chats are refused as mixed.
**Why:** A declared world must obey the same couplings as one built by calls. `deleteBusinessMessages` names no chat, because a user account numbers all its private chats from one sequence.
**Code:** `aiogram/test/blueprint.py` `Blueprint.build`; `aiogram/test/world.py` `granted_permissions`, `create_topic`, `StarTransactionState`, `ChatState.allocate_message_id` · **Source:** 2026-10-14-align-fake-api-with-bot-api

### TW-156 Forward and copy destinations are checked once per call
**Decision:** `landing()` checks the bot's standing in the chat, then the topic, in the server's order, and returns where the message lands. `forward_one`/`copy_one` take the result.
**Why:** A batch of N does not run the checks N times, and the order lives in one place.
**Code:** `aiogram/test/modeling.py` `landing`, `forward_one`, `copy_one` · **Source:** 2026-10-17-address-testing-toolkit-review

### TW-157 The bot's rights are one table, checked before the handler
**Decision:** `BOT_RIGHTS` maps a method type to a `RightRule` (right, rejection, per-chat-type rejection, chat types, precheck). `handle_call` runs `check_bot_rights` after parse modes and before the handler. `holds_right` gives the owner every right and an administrator its scoped rights. On by default; `enforce_bot_rights=False` turns it off. `require_standing` refuses a call into a non-private chat the bot left or was kicked from, before any other check. An undeclared bot membership counts as a member.
**Why:** Prechecks keep TDLib's order (owner guard first, forum check first). Rejection texts are TDLib's, lowercased at the first letter as the server relays them. The Bot API server answers with a 403 in `check_chat_access` before anything else.
**Code:** `aiogram/test/modeling.py` `BOT_RIGHTS`, `RightRule`, `check_bot_rights`, `holds_right`, `bot_has_right`, `require_standing` · **Source:** 2026-10-16-model-forum-topics-and-bot-rights

### TW-158 A topic creator's exemption applies only to topics TDLib holds
**Decision:** `_opened_by_bot` skips the rights check for an unknown or deleted topic and for a topic the bot created. The handler then answers `message thread not found` or `TOPIC_DELETED`.
**Why:** TDLib checks rights only for a cached topic it did not create, and drops a deleted topic from its cache.
**Rejected:**
- Rights checked before any lookup: not what the TDLib source does.
**Code:** `aiogram/test/modeling.py` `_opened_by_bot` · **Source:** 2026-10-17-guarantee-refusal-codes-not-texts

### TW-159 A group's unset permissions are Telegram's defaults
**Decision:** `Blueprint.build` gives a group or supergroup with `permissions=None` `default_chat_permissions()`: all messages, reactions and inviting allowed; info, pinning, topics and tags denied. Private chats and channels get nothing. The value is built through `granted_permissions`.
**Why:** `require_send_permission` and restricted narrowing read `ChatState.permissions`; "unset" must mean what a new group has.
**Code:** `aiogram/test/world.py` `default_chat_permissions`; `aiogram/test/blueprint.py` · **Source:** 2026-10-17-finish-tasks-record-routes-parse-markup

## Ephemeral messages

### TW-160 Ephemeral messages live in two per-chat stores, one per direction
**Decision:** `sent_ephemeral` (bot to user) and `received_ephemeral` (user to bot) are kept out of `messages`, keyed by user. Read with `chat.ephemeral_messages(user)` and `chat.ephemeral_commands(user)`. One per-chat counter numbers both. An incoming command has no `receiver_user`.
**Why:** `edit_ephemeral` can never land on a user's command, and reply validation can never take the bot's message as incoming. The Bot API defines `receiver_user` only for the user who received the message.
**Rejected:**
- One store with a direction flag: every reader would need to filter.
**Code:** `aiogram/test/world.py` `ChatState.sent_ephemeral`, `received_ephemeral`, `last_ephemeral_message_id` · **Source:** 2026-10-14-model-ephemeral-messages

### TW-161 Registration routes by `ephemeral_message_id`
**Decision:** A carried message with an `ephemeral_message_id` goes to the incoming store unless the id is known, and skips the shared-history id check. One without `from_user` is a `WorldLookupError`.
**Why:** Every ephemeral message has `message_id=0` and would collide in the shared history.
**Code:** `aiogram/test/environment.py` `_register_carried_message` · **Source:** 2026-10-14-model-ephemeral-messages

### TW-162 The ephemeral send path is chosen by the request, not the method
**Decision:** Any send with `ephemeral_message_parameters` (or the deprecated `receiver_user_id`) takes the ephemeral path. It refuses non-group chats, resolves the receiver through the world, requires a replied ephemeral id to name an incoming command, and refuses `replace_callback_query_message` for a callback from an ephemeral message. The result has `message_id=0`. A non-ephemeral send replying to an ephemeral id is refused.
**Why:** Fourteen methods carry the field, and future ones behave the same. The group-only rule comes from the deprecated `receiver_user_id` text.
**Code:** `aiogram/test/modeling.py` `_ephemeral_receiver`, `build_message`; `aiogram/test/world.py` `World.ephemeral_callbacks` · **Source:** 2026-10-14-model-ephemeral-messages

### TW-163 The ephemeral edit and delete family is modeled
**Decision:** `editEphemeralMessage*` update the stored message via `derive_message`; `deleteEphemeralMessage` removes it. A target missing for that chat and receiver fails. Each returns `True`. Regular `editMessage*` on `message_id=0` fails with no special case. `RECORD_ONLY` keeps drafts only for this area.
**Why:** The stores give these calls real state to act on.
**Code:** `aiogram/test/modeling.py` ephemeral handlers, `RECORD_ONLY` · **Source:** 2026-10-14-model-ephemeral-messages

### TW-164 Clicks see the actor's ephemeral messages first; a miss names where the button is
**Decision:** The button search covers the outgoing messages addressed to the actor, newest first, then the shared history. On a miss, the hint also names another receiver in the same chat. `_misdirected_callback_hint` scans every other chat only after the actor's own chat fails, exhaustively.
**Why:** An ephemeral message is the more specific target, and `message_id=0` cannot be ordered by id. The cost lands only on the failure path; a heuristic hit in the wrong chat is worse than no hint.
**Code:** `aiogram/test/actors.py` `_visible_messages`, `_misdirected_callback_hint` · **Source:** 2026-10-14-model-ephemeral-messages, 2026-08-25-target-overrides-and-diagnose-routing

### TW-165 `send(ephemeral=True)` is an explicit flag
**Decision:** The actor marks a command ephemeral only when asked. It refuses outside groups and supergroups and with a business binding (`WorldLookupError`). In a topic-bound actor the command carries the thread.
**Why:** `BotCommand.is_ephemeral` is per scope and language; a test that wants an ephemeral message says so.
**Code:** `aiogram/test/actors.py` `UserActor.send` · **Source:** 2026-10-14-model-ephemeral-messages

## Rich messages

### TW-166 Rich input converts to stored content by reflection
**Decision:** `InputRich*X` converts to `Rich*X` from `aiogram.types`. Per field: same annotation is carried; nested `InputRich*` converts recursively; `InputMedia*` is synthesized non-empty (`nonempty`, shared with `sendPhoto`); a required unset field gets its zero value; `type` is never carried. A guard test walks the graph from `InputRichMessage.blocks`.
**Why:** A Bot API bump that adds a block type needs no change. Zero values are valid in every documented range.
**Rejected:**
- Synthesize then carry request values recursively: cannot build a paragraph, drops text and buttons.
- A converter table per block type: 26 entries per bump, and a missing one drops content silently.
**Code:** `aiogram/test/rich.py` `counterpart`; `aiogram/test/synthesis.py` `nonempty` · **Source:** 2026-10-14-model-rich-message-content

### TW-167 A text edit replaces the content kind
**Decision:** `handle_edit_text` sets either `text`/`entities` or `rich_message` and clears the other. Markup handling is unchanged.
**Why:** An edit carrying only `rich_message` cleared the text and dropped the content.
**Code:** `aiogram/test/modeling.py` `handle_edit_text` · **Source:** 2026-10-14-model-rich-message-content

### TW-168 Buttons are found by an ordered walk of the model tree
**Decision:** The button walk covers `reply_markup` then `rich_message`, depth-first in document order, iteratively. It yields `InlineKeyboardButton` and `RichMessageButton`. `click` and `follow_deep_link` accept either.
**Why:** Rich text nests through many block kinds; a typed walk would be a hand-kept list again.
**Rejected:**
- A typed walk over `RichBlockButtons`/`RichTextButton`.
**Code:** `aiogram/test/actors.py` `_iter_buttons`, `_buttons_of` · **Source:** 2026-10-14-model-rich-message-content

## Restricted membership

### TW-169 Presence is stored only for restricted users
**Decision:** `MemberState.is_member` is read only while `RESTRICTED`. `is_present` is not left, not kicked, and not restricted-and-absent.
**Why:** It is the one status whose Bot API variant carries presence.
**Rejected:**
- A general `is_present` field: two sources of truth for "left".
**Code:** `aiogram/test/world.py` `MemberState.is_member`, `is_present` · **Source:** 2026-10-14-report-restricted-membership-truthfully

### TW-170 One status helper keeps presence, end dates and titles consistent
**Decision:** `set_status` keeps presence when moving into `RESTRICTED`, clears `until_date` on a move into a status other than restricted or banned, and clears the custom title outside admin statuses. Join and leave on a restricted user flip `is_member`, giving a restricted-to-restricted update. A ban in a basic group stores no end. A missing end reads as `1970-01-01 UTC` (`UNTIL_FOREVER`). `unbanChatMember` with `only_if_banned` does nothing for a user who is not banned; otherwise it moves the user to `LEFT`.
**Why:** The Bot API says a restriction survives leaving, and reads `until_date` on other statuses as a subscription expiry. aiogram parses `0` as the epoch, which is what a bot reads. Removing a present member is the documented default.
**Code:** `aiogram/test/world.py` `MemberState.set_status`, `join_or_leave`, `UNTIL_FOREVER`, `as_chat_member`; `aiogram/test/modeling.py` `handle_unban` · **Source:** 2026-10-14-report-restricted-membership-truthfully

### TW-171 Granting every permission lifts a restriction
**Decision:** After `granted_permissions`, a mask with every `ChatPermissions` field true lifts it: present users become `MEMBER`, absent ones `LEFT`. The check reflects over `model_fields`.
**Why:** A permission added by a later Bot API is included automatically.
**Code:** `aiogram/test/modeling.py` `handle_restrict`; `aiogram/test/world.py` `lift_restriction` · **Source:** 2026-10-14-report-restricted-membership-truthfully

## Membership triggers

### TW-172 `join()`/`add_bot()` post `new_chat_members` in groups, after the membership update
**Decision:** Only in a group or supergroup, after `chat_member`. The trigger returns the membership update's result. `service_message=True` by default; `False` suppresses it.
**Why:** Telegram clients show the transition, then the announcement. Private chats and channels have no such service message.
**Code:** `aiogram/test/actors.py` `join`, `add_bot`, `_MEMBER_SERVICE_MESSAGE_CHAT_TYPES` · **Source:** 2026-08-25-target-overrides-and-diagnose-routing

### TW-173 `promote()`/`demote()` default to the bot, and rights are the whole mask
**Decision:** `promote(subject=None, *, data=None, deliver=True, **rights)` sets exactly the rights passed; a bare `promote()` still promotes. `demote(subject=None, *, data=None, deliver=True)` clears rights and title, keeps `tag`. Unknown rights raise `TypeError`, like `_validated_fields`.
**Why:** Promoting the bot is what group tests do first. `data=` on both frees `**rights` and removes the `promote`/`demote` asymmetry.
**Code:** `aiogram/test/actors.py` `promote`, `demote`, `_validate_rights` · **Source:** 2026-08-25-target-overrides-and-diagnose-routing, 2026-08-25-review-wave-4-hardening

## Background tasks and draining

### TW-174 `drain()` is opt-in, and task protection is extended at the first asynchronous entry
**Decision:** A test calls `await env.drain()`. `dispose`/`dispose_sync` never drain. Tasks alive at construction and at the first `feed`/`handle_call` are spared, except the entering task. On an environment that never ran, `drain()` returns `0`.
**Why:** `dispose_sync` cannot await, so auto-drain would work on one teardown path only. Cancelling unmentioned tasks hides "my scheduler stopped". `bot_env` is synchronous, so the construction snapshot is usually empty and a session fixture's worker would be cancelled.
**Rejected:**
- Re-snapshot on every call: would spare tasks the bot spawned later.
- Letting the task factory decide what to cancel: a larger change than the gap needed.
**Code:** `aiogram/test/environment.py` `drain`, `dispose_sync`, `_protect_running_tasks` · **Source:** 2026-08-25-target-overrides-and-diagnose-routing, 2026-08-25-review-wave-4-hardening

### TW-175 The loop's task factory is wrapped to see finished tasks
**Decision:** The wrapper delegates to the previous factory, records each task and its creator, and adds a done-callback. Succeeded and cancelled tasks are forgotten; a task with an unretrieved failure (`_log_traceback`, read with `getattr(..., True)`) is held strongly until retrieved. Restore is by identity and skips disposed environments.
**Why:** `asyncio.all_tasks()` hides finished tasks. Only the flag tells a failure the bot handled from one nobody saw.
**Rejected:**
- Keeping a failure record and releasing the task: would report failures the bot catches a moment later.
**Code:** `aiogram/test/environment.py` `_track_spawned_tasks`, `_forget_task`, `_unretrieved`, `_untrack_spawned_tasks` · **Source:** 2026-08-25-review-wave-4-hardening, 2026-10-17-finish-tasks-record-routes-parse-markup, 2026-10-14-align-actor-triggers-with-bot-api

### TW-176 A task's own failure is raised, never swallowed
**Decision:** Failures are raised as `DrainedTaskError` (a `BackgroundTaskError`), first one chained as `__cause__`. A task still running after cancellation raises `WaitTimeoutError`, carrying any failures and the chain.
**Why:** Discarding the exception would make `drain()` hide real bugs.
**Code:** `aiogram/test/environment.py` `drain`; `aiogram/test/errors.py` `BackgroundTaskError`, `DrainedTaskError` · **Source:** 2026-08-25-review-wave-4-hardening, 2026-10-17-finish-tasks-record-routes-parse-markup

### TW-177 Waiting for tasks uses the same task set as `drain()`
**Decision:** `wait_for_background_tasks()` and `drain()` share `_own_tasks()`, which spares the caller and every task awaiting or having created it. The wait repeats until nothing is pending, against one loop-clock deadline; a timeout names each task and cancels nothing.
**Why:** Some work should finish, not be cancelled. A call from a child task must not wait for or cancel the test that awaits it.
**Code:** `aiogram/test/environment.py` `wait_for_background_tasks`, `_own_tasks`, `_spared_tasks` · **Source:** 2026-10-17-finish-tasks-record-routes-parse-markup

## Markup parsing

### TW-178 Parse modes are applied in one pass before the handler
**Decision:** `apply_parse_modes()` walks the resolved call and returns a copy with plain text. `parse_mode` formats `text`, `message_text`, `caption` or `title`; `x_parse_mode` formats `x`; entities are `x_entities`, else `entities`. It runs for modeled methods after overrides; the call log keeps the call as made.
**Why:** The Bot API server parses before Telegram sees the request. The naming rule covers every type without a table.
**Code:** `aiogram/test/markup.py` `apply_parse_modes`; `aiogram/test/environment.py` `handle_call` · **Source:** 2026-10-17-finish-tasks-record-routes-parse-markup

### TW-179 The parsers are TDLib ports
**Decision:** A parse mode other than empty or `none` on non-empty text wins over explicit entities (`get_formatted_text`); an unknown mode fails. HTML, MarkdownV2 and Markdown are ported from TDLib over UTF-8 bytes, with TDLib's errors behind `Can't parse entities: `. Links follow `check_link`; a mention of an undeclared user is dropped. Only part of `fix_formatted_text` is modeled. Text rendered by `html_decoration`/`markdown_decoration` must parse back unchanged, except HTML `pre` with `language=` and the MarkdownV2 custom-emoji link with `emoji_id=`.
**Why:** Byte offsets and texts then match what the server reports. Those two renderings do not match Telegram's grammar.
**Code:** `aiogram/test/markup.py`; `tests/test_testing/test_markup.py` · **Source:** 2026-10-17-finish-tasks-record-routes-parse-markup

### TW-180 Actor texts get command entities by TDLib's matcher
**Decision:** `bot_command_entities()` ports `match_bot_commands`. The actor marks `text` and `caption` after `fields`; an explicit `entities` (even `[]`) stands. Only commands are added. The bot's own sends are untouched.
**Why:** A client marks commands on what it sends; the server does not mark the bot's text.
**Code:** `aiogram/test/markup.py` `bot_command_entities`; `aiogram/test/actors.py` `_build_message` · **Source:** 2026-10-17-finish-tasks-record-routes-parse-markup

## Other senders, anonymous admins and withheld updates

### TW-181 Another bot is a user with `is_bot`
**Decision:** `add_user(..., is_bot=True)` declares another bot actor. `bot_to_bot_mode` is on `UserSpec`/`UserState`; the bot under test takes it and `bot_group_privacy` from `Blueprint(...)`. A person with `bot_to_bot_mode` is a `ValueError`. `getMe` reports `can_read_all_group_messages = not bot_group_privacy`; `World.bot_me()` builds it and `World.__setattr__` refreshes the bot's cached user.
**Why:** Every rights check a user actor meets then applies to another bot unchanged.
**Code:** `aiogram/test/blueprint.py` `UserSpec`; `aiogram/test/world.py` `World.bot_me`, `World.__setattr__` · **Source:** 2026-10-17-model-other-senders-topic-creators-and-lost-updates, 2026-10-17-address-testing-toolkit-review

### TW-182 One function decides whether Telegram delivers another bot's message
**Decision:** `_withheld_by_telegram` looks only at a `message`/`edited_message` from another bot posting as itself, in a group. It passes a command naming the bot or a direct reply with the mode on either side, or everything with the mode on the bot's side when the bot is admin or privacy is off. In a private chat both sides need the mode, else `WorldLookupError` before storing. `deliver_service_messages_from_bots` defaults to `True`. A message is a service message when its `content_type` is none a user can post.
**Why:** It is the rule core.telegram.org/bots/features states. No source says what Telegram sends; the content-type rule also covers service messages a test builds with `fields=`.
**Code:** `aiogram/test/actors.py` `_withheld_by_telegram`, `_reaches_bot`, `_addresses_bot`, `_is_service`; `aiogram/test/environment.py` · **Source:** 2026-10-17-model-other-senders-topic-creators-and-lost-updates

### TW-183 A withheld update is stored, adopted and returned as `Withheld`
**Decision:** The world changes as usual; the trigger returns `Withheld(update, reason)` whose repr names update id, kind and reason. The update goes through `adopt()`, and an empty route scope opens so routes do not report the previous trigger.
**Why:** Nothing is routed, so the unhandled check sees nothing; shortcuts on the update still work.
**Code:** `aiogram/test/actors.py` `Withheld`, `_feed`; `aiogram/test/environment.py` `adopt` · **Source:** 2026-10-17-address-testing-toolkit-review, 2026-10-17-model-other-senders-topic-creators-and-lost-updates

### TW-184 `deliver=` is a keyword of every trigger that feeds an update
**Decision:** `deliver` sits next to `**data` (or `data=`), is checked first in `_feed`, and its reason wins. The world changes before `_feed` either way. `create_topic()` returns the topic; `delete_topic()`/`set_topics()` take no keyword.
**Why:** A keyword reads at the call that loses the update and cannot leak to the next trigger.
**Rejected:**
- An actor-level switch such as `alice.withholding()`.
**Code:** `aiogram/test/actors.py` (`deliver: bool = True` on triggers) · **Source:** 2026-10-17-model-other-senders-topic-creators-and-lost-updates

### TW-185 An anonymous administrator is a binding
**Decision:** `in_(chat, anonymous=True)` keeps the user and its rights and changes only the sender: `GroupAnonymousBot` (id 1087968824) with the chat as `sender_chat`, built fresh per message. `author_signature` is the custom title, on regular messages only. It needs a supergroup and an admin with `is_anonymous`, checked when binding and at each trigger start (`_trigger`). Join and leave refuse it.
**Why:** This is the Bot API server's `create_message` mapping run backwards; TDLib sets `author_signature` only on a `message`.
**Code:** `aiogram/test/actors.py` `in_`, `_trigger`, `_require_anonymous`; `aiogram/test/world.py` `posted_by` · **Source:** 2026-10-17-model-other-senders-topic-creators-and-lost-updates, 2026-10-17-address-testing-toolkit-review

### TW-186 Only what is posted as the group hides the user
**Decision:** Clicks and queries from an anonymous binding keep `from_user` and the user's FSM key. Reactions and votes name the chat as `actor_chat`/`voter_chat`. A topic opened anonymously belongs to the admin. `PollState.chat_id` is set by `sendPoll`, a declared poll and a copy. A poll without one is not held against an anonymous vote. A forward keeps the original's poll.
**Why:** Telegram shows who pressed. `MessageReactionUpdated` and `PollAnswer` document the chat for an anonymous user. TDLib's creator is the account. The vote rules for anonymous bindings need the poll's chat.
**Code:** `aiogram/test/actors.py`; `aiogram/test/world.py` `PollState.chat_id` · **Source:** 2026-10-17-model-other-senders-topic-creators-and-lost-updates, 2026-10-17-address-testing-toolkit-review

## Flood control

### TW-187 Flood limits are opt-in, a sliding window per chat that counts messages
**Decision:** `BotTestEnvironment(rate_limits=RateLimits())` turns them on (default: 1/s per chat, 20/min per group). `retry_after` is the time until the oldest send keeping the chat over a limit leaves its window, rounded up. The clock is `loop.time()` plus how far `advance_time` moved. A refusal is the real `TelegramRetryAfter`. A modeled send calls `admit_send(chat, messages=n)` after its local checks and before changing the world; `handle_call` records `n` stamps after the handler succeeds. A call under the limit may take it over.
**Why:** Waiting exactly `retry_after`, by either clock, must be enough. The FAQ speaks of messages; counting every album item is the cautious reading. An album of ten could never fit one per second otherwise.
**Code:** `aiogram/test/flood.py` `RateLimits`, `FloodControl`, `RATE_LIMITED_METHODS`; `aiogram/test/environment.py` `rate_clock`, `admit_send`, `handle_call` · **Source:** 2026-10-16-model-forum-topics-and-bot-rights, 2026-10-17-address-testing-toolkit-review

## Non-goals and known limits

- The toolkit does not run the webhook HTTP layer or the polling loop. Both reduce to `feed_update`; webhook and `getUpdates` methods are record-only.
- No real network, real tokens, or record/replay against live Telegram.
- No load or concurrency testing.
- No media processing. A sent photo becomes a `PhotoSize` with a plausible id; no bytes are read, no dimensions or thumbnails derived.
- `FSInputFile` and `URLInputFile` are never read. There are no real paths, MIME types, size limits, `file_path` expiry or 20 MB ceiling.
- Sticker files are not downloadable content. Per-sticker attribute setters and set thumbnails are record-only. The 120-sticker limit is not enforced.
- Payments: `sendInvoice` stores an `Invoice`; there is no order or payment flow beyond the actor triggers. Payment trigger order is not enforced.
- Stars: no commission, payout schedule, hold or currency conversion. Affordability is not checked. A unique gift is an owned gift with a flag, not a collectible.
- Business bot rights (`can_reply`, `BusinessBotRights`) are stored, not enforced.
- Direct messages topics are not modeled.
- Communities have no methods; only declaration and service messages.
- `getMyCommands` does not model which commands a given user sees. Command names and description lengths are not validated. The bot's profile photo is record-only.
- Invite links are metadata. Joining via a link, `member_limit`, and join-request counts are not modeled; actors join chats directly.
- Quizzes are not scored and explanations are not revealed.
- `chat_boost`, `subscription` and `managed_bot` triggers produce the update; there is no boost or subscription economy behind them.
- Synthesized results can be semantically odd while schema-valid. Tests that care declare an override.
- `RECORD_ONLY` is not exhaustive. A new method in an excluded family is unmodeled and unlisted until someone adds it.
- Deep links: Mini Apps, group/channel choosers and the attachment menu are not simulated. A link to another bot is refused. Invite links are not followed into membership.
- Topic-filtered views are O(n) per access.
- The waiting helpers do not control event-loop time. A bot whose engine sleeps 30 s makes the wait take 30 s; time-control libraries such as `looptime` are a documented composition, not a dependency.
- Waits are on world state, not on API calls.

## Open questions and future work

- Should `bindables` be public? It is still exported only from `aiogram.test.mounting`.
- Should `NoFileContentError` fold into `WorldLookupError`? It stays a separate type carrying `file_id`.
- Should `chat.ephemeral_messages()` with no user return every receiver's messages? It still requires a user.
- The ephemeral group-only rule comes from deprecated `receiver_user_id` text; a valid non-group call would be refused if Telegram allows it.
- Whether an incoming ephemeral command carries `receiver_user` is undocumented; it is left unset.
- Ephemeral message expiry is undocumented; ids are never reused. Actors cannot edit or reply to an ephemeral target.
- Invite-link `expire_date`/`member_limit` are stored but not enforced: joining by link is not modeled.
- Subscription renewal (`subscription_period`), the 24-hour "active chat" rule, `sendChatAction` status and callback/inline answer timeouts are not modeled.
- Join-request queries and their 10-second window are not modeled.
- If Telegram is shown to send `chat_member` on restriction expiry, it would join the due-event queue.
- The poll-close `poll` update, batch deletion skipping protected messages and `until_date` ignored in basic groups are the toolkit's readings.
- The restricted-to-restricted update on leave is inferred from `is_member` wording.
- A stale `message_thread_id` after topics are turned off is stored untagged; this is read from server source, not documented.
- Group default permissions are what clients show for a new group, not a documented list.
- Inline query `chat_type` for chats the actor is not bound to cannot be expressed.
- A sticker's media type is not matched to its `InputSticker.format`.
- Rich `html`/`markdown` input is not parsed into blocks, and `InputRichMessage.media` links are not resolved.
- Zero values for unset required rich fields are a choice, not Telegram's documented fill-in.
- `<tg-time>`/`tg://time` refusal texts are the toolkit's; nested captions fail with the top-level description.
- Only part of TDLib's `fix_formatted_text` is modeled; actors auto-mark commands only, not mentions, hashtags or links.
- A time-control mode for fast sleeps is undesigned; it needs a way to tell bot timers from driver timers.
- `drain()` protection is a heuristic: a bot task created from a fixture before the first feed is spared, and another test's fixture task created later is not.
- A done task stays in the running set for one loop turn, so a drain in that gap sees it.
- The loop-scoped cache hazard (a middleware's client bound to a dead loop) is not addressed by the toolkit; the docs name it.
- Album counting for flood limits is an assumption; Telegram's burst tolerance is not modeled.
- Bot-to-bot: delivery into a business chat, the topic-root implicit reply not counting as a reply, `chat_member` updates caused by an anonymous admin, and the reported creator of an anonymously opened topic are unverified assumptions.
- A declared topic with no creator is no one's while its root is from the bot; the docs point at `creator=blueprint.bot`.
- No refusal text is a contract; tests should assert the exception type.

## Superseded (not carried over)

Decisions the archived change sets made that the code does not follow, with the reason.

- "Shape, not policy: permissions and admin rights are never enforced" (add-bot-testing-toolkit, model-chat-administration, declare-bot-status-and-member-rights): `BotTestEnvironment(enforce_bot_rights=True)` is the default and `check_bot_rights`/`require_send_permission` refuse calls the bot's standing does not allow.
- "Errors only where a test would provoke them; everything else permissive" (model-chat-administration D4): `rejections.py` holds a sourced catalogue of refusals well beyond that list.
- "Topic permissions and `can_manage_topics` are not enforced" (extend-testing-toolkit-api-surface): topic methods have right rules (`NO_RIGHTS_TO_CREATE_TOPIC` and others).
- "Invite links skip `can_invite_users` checks" (model-invite-links): invite-link methods use the `_INVITING` right rule.
- "Rate limits are out of scope" (add-bot-testing-toolkit): `RateLimits` models per-chat flood limits, opt-in.
- "Message-age limits on edit/delete are out of scope" (add-bot-testing-toolkit): 48 h delete and business edit windows are modeled.
- "No clock; query expiry is never time-based" (complete-actor-triggers): `World.now` with `advance_time`, and `ANSWER_WINDOWS` gives pre-checkout queries 10 s.
- "Draining or cancelling the bot's background tasks is not the toolkit's business" (add-waiting-helpers): `drain()` and `wait_for_background_tasks()` exist.
- "An anonymous poll still records which actor voted" (model-polls-and-reactions): `vote()` refuses anonymous polls.
- "No restriction on a second quiz attempt" (model-polls-and-reactions): a changed vote is refused unless the poll `allows_revoting`.
- "Ephemeral messages stay record-only" (complete-message-method-modeling): the ephemeral edit/delete family is modeled; only drafts are in `RECORD_ONLY`.
- "Sender-chat forward origin is not implemented" (complete-message-method-modeling D8): `MessageOriginChat` is produced. The hidden-user origin is still not.
- "A sent `file_id` stays synthesized rather than echoed" (complete-message-method-modeling D7): a passed file id replaces the synthesized one (`with_passed_file`).
- "Batch forward/copy delegate to the single handler and raise `TelegramBadRequest` for an unknown source chat" (complete-message-method-modeling D3): they share per-message helpers, and an unknown chat is a `WorldLookupError`.
- "`getChatMemberCount` is `len(members)`" (model-chat-administration D3): it counts `present_members()`.
- "`Blueprint` and its members are frozen dataclasses" (add-bot-testing-toolkit D6): `Blueprint` is a mutable builder; isolation comes from deep-copying in `build()`.
- "The world stores `MessageRecord`s" (add-bot-testing-toolkit D5): stored messages are `aiogram.types.Message` objects.
- "`detach_router` clears parents recursively" (add-bot-testing-toolkit D7): it clears only the given router's `_parent_router`.
- "A `pytest11` entry point auto-loads the plugin" (add-bot-testing-toolkit D9): the plugin is opt-in; `pyproject.toml` has no `pytest11` entry.
- "`start` wins whenever present" (follow-deep-links D3, wave-2 D2): only a non-empty `start` wins.
- "`_QUERY_PARAM_KINDS` is the complement of `_PATH_DERIVED_KINDS`" (follow-deep-links D2, D6): replaced by `_QUERY_KIND_LOOKUP` and `_LinkKindPolicy.match_by`.
- "`addresses_username` marks the family of a link kind" (classify-links-per-spec D1): replaced by `match_by`, which also handles `attach` naming the bot in its payload.
- "Deferred clusters are named in `RECORD_ONLY` with a sentence each" (specify-record-only-boundary D4): stars/gifts and sticker sets are modeled; stories and business profile are left out of the list on purpose.
- "Multi-bot environments and cross-bot interaction are out of scope" (add-bot-testing-toolkit): other bots can be declared as users (`add_user(is_bot=True, bot_to_bot_mode=...)`), and messages carried in from another environment are registered.
- `w2.chats = w1.chats` rewraps the foreign registry into one wired to `w2` (harden-wave-3-edges D1): replaced by a loud refusal (TW-126).
- `w2.chats = dict(w1.chats)` shares and rewires the chat objects (target-overrides D9): `ChatRegistry.__setitem__` refuses foreign-owned chats (TW-125).
- `last_route` reports only the last fed update, cleared at each `feed` (target-overrides D3): replaced by trigger scopes (TW-140, TW-141).
- Rejected "keep a full log of every route" (review-wave-4 D2, target-overrides D3): `all_routes` keeps every frame (TW-143).
- `_guard_not_owner` raises `ApiRejection("can't remove chat owner")` (target-overrides D6): it raises `WorldLookupError` (TW-112).
- `promote(subject=None, **rights)` / `demote(**data)` (target-overrides D6): dispatcher data goes through `data=` on both (TW-173).
- `drain()` protects only tasks alive at construction (target-overrides D8): extended at first async entry (TW-174).
- `wait_for_tasks()` and `drain()` leave out the task that made the first entry (finish-tasks D1): that task is not spared; the caller and its awaiters are (TW-177). Also renamed `wait_for_background_tasks`.
- `route_history` / `expect_unhandled()` (finish-tasks D2): named `all_routes` / `assert_unhandled()`.
- Rights checked in each handler by `require_pin_right`, `require_restrict_right`, `require_promote_right` (forum D4): one `BOT_RIGHTS` table checked in `handle_call` (TW-157).
- "Not checked: chat settings and topic management rights, a bot that has left" (forum D4): `BOT_RIGHTS` covers title, description, photo, sticker set, invite links and forum methods; `require_standing` refuses a bot that left.
- "A member whom chat permissions let manage topics is not modeled as holding the right" (forum D7): creating a topic accepts the chat permission (`may_create_topics`).
- `ChatState.api_topic()` (forum D1): named `topic_for_call()`.
- Flood check read in `handle_call` before the handler (forum D6): the handler calls `admit_send` after its own checks (TW-187).
- Declared topics created with the bot as `from_user` (fake-api D7): the declared creator posts the root; the bot only when no creator is set (TW-43).
- Cross-chat replies not synthesized as `external_reply` (fake-api non-goal): `_reply_changes` builds `external_reply` for a reply in another chat.
- `ChatState.topic()` raises `ApiRejection` for both bot and test (forum context): split into two lookups (TW-38).
