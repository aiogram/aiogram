## 1. FSM key correction (ship first — it is a defect, not a feature)

- [x] 1.1 Extend `BotTestEnvironment.state()` with keyword-only `topic=` and `business_connection=`, forwarding `thread_id` / `business_connection_id` into `FSMContextMiddleware.resolve_context`
- [x] 1.2 Add `UserActor.state()` filling both from the actor's binding
- [x] 1.3 Regression test: under `FSMStrategy.USER_IN_TOPIC`, data written by a handler for a topic event is readable through `env.state(..., topic=...)` — the case that currently returns an empty context
- [x] 1.4 Regression test: the same for `CHAT_TOPIC`, and for a business connection key

## 2. Topic world state

- [x] 2.1 Add `TopicState` (thread id, name, icon colour, icon custom emoji, `is_closed`, `is_general`, `is_hidden`) to `world.py`
- [x] 2.2 Add `ChatState.is_forum`, `ChatState.topics`, `ChatState.general_topic`, and `ChatState.topic(thread_id)` lookup
- [x] 2.3 Implement `TopicState.messages` as a filtered view over `ChatState.messages` (design D11 — no second list)
- [x] 2.4 Implement topic creation as "allocate a message id, emit the service message, use that id as the thread id" (design D12)
- [x] 2.5 Tests: topic registry, filtered views, General topic messages carry no thread id

## 3. Topic declaration

- [x] 3.1 Add `Blueprint.add_topic(chat, name, ...)` returning a handle, marking the chat as a forum
- [x] 3.2 Materialize declared topics through the same path as created ones, so declared and API-built worlds are indistinguishable
- [x] 3.3 Tests: declaration, isolation between environments, `Chat.is_forum` reaches handlers

## 4. Forum methods

- [x] 4.1 Model `CreateForumTopic`, `EditForumTopic`, `CloseForumTopic`, `ReopenForumTopic`, `DeleteForumTopic`
- [x] 4.2 Emit `forum_topic_created`, `forum_topic_edited`, `forum_topic_closed`, `forum_topic_reopened` service messages
- [x] 4.3 Model `UnpinAllForumTopicMessages` and `UnpinAllGeneralForumTopicMessages`
- [x] 4.4 Model the General family: `EditGeneralForumTopic`, `CloseGeneralForumTopic`, `ReopenGeneralForumTopic`, `HideGeneralForumTopic`, `UnhideGeneralForumTopic`, emitting `general_forum_topic_hidden` / `general_forum_topic_unhidden`
- [x] 4.5 Fail with `TelegramBadRequest` when posting into or acting on an unknown or deleted topic (design D13)
- [x] 4.6 Leave `GetForumTopicIconStickers` on the synthesize path and assert it still answers
- [x] 4.7 Tests per method: resulting topic state, the emitted service message, and the error paths

## 5. Topic addressing for actors

- [x] 5.1 Add keyword-only `topic=` to `UserActor.in_()`, returning a new bound actor
- [x] 5.2 Tag every trigger the bound actor produces with `message_thread_id` and `is_topic_message`
- [x] 5.3 Verify `message.answer()` replies inside the topic (the `.butcher` alias fill already handles this — assert it end to end)
- [x] 5.4 Tests: binding does not mutate the source actor; replies land in the right topic; two topics stay separate

## 6. Business connection world state

- [x] 6.1 Add `BusinessConnectionState` (id, owner user id, `user_chat_id`, `is_enabled`, `can_reply`, rights) and `World.business_connections`
- [x] 6.2 Add `Blueprint.add_business_connection(owner, ...)` returning a handle
- [x] 6.3 Model `GetBusinessConnection` from state; fail on an undeclared id
- [x] 6.4 Model `ReadBusinessMessage` and `DeleteBusinessMessages` against the world
- [x] 6.5 Leave the business *account* methods (`SetBusinessAccountName`, `GetBusinessAccountGifts`, `TransferBusinessAccountStars`, …) on the synthesize path and assert they still answer
- [x] 6.6 Tests: declaration, isolation, modeled methods, unknown-connection error

## 7. Business sender attribution

- [x] 7.1 In `build_message`, attribute a message carrying a known `business_connection_id` to the connection owner, with `sender_business_bot` set to the bot (design D15)
- [x] 7.2 Carry `business_connection_id` onto the stored message
- [x] 7.3 Tests: business send is attributed to the owner; ordinary send is still attributed to the bot; the call log still records the outgoing method unchanged

## 8. Business triggers

- [x] 8.1 Add keyword-only `business=` to `UserActor.in_()`; a bound actor's `send`/`edit` produce `business_message` / `edited_business_message`
- [x] 8.2 Add `actor.enable_business_connection()` / `disable_business_connection()` producing `business_connection` updates and updating the declared state
- [x] 8.3 Add a trigger for `deleted_business_messages` that also removes the messages from the chat
- [x] 8.4 Tests: each update type reaches its handler, `event_from_user` resolves, and world state follows

## 9. Communities

- [x] 9.1 Add `CommunityState` and `Blueprint.add_community(name)`; allow attaching chats to it
- [x] 9.2 Surface the community on `ChatFullInfo.community` from the modeled `GetChat`
- [x] 9.3 Add actor triggers `add_chat_to_community` / `remove_chat_from_community`, storing the service message in the chat and updating attachment state
- [x] 9.4 Tests: declaration, `getChat` exposure, both service messages, attachment state after each

## 10. Documentation

- [x] 10.1 Add a "Forum topics" section to `docs/dispatcher/testing.rst` covering declaration, addressing and the modeled methods
- [x] 10.2 Add a "Business connections" section, including the sender-attribution behavior and the explicit non-enforcement of rights
- [x] 10.3 Add a "Communities" section
- [x] 10.4 Update the FSM section with `topic=` / `business_connection=` and remove the now-fixed caveat
- [x] 10.5 Build docs and fix any new warnings

## 11. Release readiness

- [x] 11.1 `CHANGES/<issue-or-pr>.feature.rst`, calling out the business sender-attribution change explicitly as a behavior correction
- [x] 11.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing` at 100%
- [x] 11.3 Verify the new suite runs without `--redis` / `--mongo` and stays inside the Python 3.10 floor
- [x] 11.4 Confirm the synthesis guard over every generated return type still passes, proving unmodeled methods keep working
