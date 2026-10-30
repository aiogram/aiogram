## MODIFIED Requirements

### Requirement: Another bot can be declared and act

A blueprint SHALL declare another bot with `add_user(..., is_bot=True)`. Another bot's actor
SHALL produce messages and service messages from it, with `is_bot` set, and SHALL be held to
the rights checks of a user actor. A trigger only a person produces SHALL raise
`WorldLookupError` for it, since the Bot API gives a bot no way to do it.

#### Scenario: A bot without the right closes a topic

- **WHEN** another bot that lacks `can_manage_topics` closes a topic
- **THEN** the trigger raises `WorldLookupError` naming the right, and the topic stays open

#### Scenario: A bot presses a button

- **WHEN** another bot's actor clicks a button
- **THEN** the trigger raises `WorldLookupError`, and nothing is fed

#### Scenario: A bot pays

- **WHEN** another bot's actor calls `pay()`
- **THEN** the trigger raises `WorldLookupError`, no charge is recorded and nothing is fed

#### Scenario: Every person-only trigger

- **WHEN** another bot's actor calls `inline_query()`, `chosen_inline_result()`, `vote()`,
  `pre_checkout_query()`, `shipping_query()`, `purchase_paid_media()`, `boost()`,
  `remove_boost()`, `update_subscription()` or `follow_deep_link()`
- **THEN** each raises `WorldLookupError`, and nothing is fed

### Requirement: The bots' own settings are declared

`add_user(..., bot_to_bot_mode=...)` SHALL declare another bot's Bot-to-Bot Communication
Mode, which only a bot SHALL take, and `Blueprint(bot_to_bot_mode=...)` the bot's own, off by
default. `Blueprint(bot_group_privacy=...)` SHALL declare the bot's Group Privacy, on by
default, and `getMe` SHALL report `can_read_all_group_messages` as its negation. The bot's
cached `me()` SHALL report the same, also after `World.bot_group_privacy` is changed.

#### Scenario: A person with the mode

- **WHEN** a blueprint declares a user who is not a bot with `bot_to_bot_mode=True`
- **THEN** the declaration raises `ValueError`

#### Scenario: Group Privacy off

- **WHEN** a blueprint declares `bot_group_privacy=False` and the bot calls `getMe`
- **THEN** `can_read_all_group_messages` is true

#### Scenario: Group Privacy changed later

- **WHEN** a test sets `world.bot_group_privacy = False` and the bot calls `getMe` and `me()`
- **THEN** both report `can_read_all_group_messages` as true, and `me()` makes no call

### Requirement: Only an anonymous administrator binds anonymously

Binding anonymously SHALL raise `WorldLookupError` outside a supergroup and for a user who is
not the owner or an administrator with `is_anonymous` set. Every trigger of the binding SHALL
recheck that the user still is, once, as it starts, and SHALL raise before changing anything
if not. Joining, leaving or asking to join SHALL raise `WorldLookupError` for the binding.

#### Scenario: A plain administrator

- **WHEN** an administrator without `is_anonymous` is bound anonymously
- **THEN** the binding raises `WorldLookupError` naming how to grant it

#### Scenario: Anonymity taken away later

- **WHEN** a bound anonymous administrator loses `is_anonymous` and then promotes a member
- **THEN** the trigger raises `WorldLookupError`, and the member is not promoted

#### Scenario: An anonymous administrator demotes themself

- **WHEN** a bound anonymous administrator with `can_promote_members` demotes themself
- **THEN** the demotion completes and `chat_member` is delivered, and only the binding's next
  trigger raises `WorldLookupError`

### Requirement: Each update of an anonymous binding names the right sender

`state()` of an anonymous binding SHALL use the FSM key of `GroupAnonymousBot`. A reaction or
a vote it makes SHALL name the chat as `actor_chat` or `voter_chat` and no user, and SHALL be
kept as the chat's. It SHALL raise `WorldLookupError` for a poll sent to another chat. A click, an inline query and the other queries SHALL come from the user,
whose FSM key `env.state(user, chat)` reads.

#### Scenario: An anonymous reaction

- **WHEN** an anonymous administrator reacts to a message
- **THEN** `message_reaction` has the chat as `actor_chat` and no `user`

#### Scenario: An anonymous vote in another chat's poll

- **WHEN** an anonymous administrator votes in a poll sent to another chat
- **THEN** the trigger raises `WorldLookupError`, and the poll keeps its votes

#### Scenario: An anonymous administrator presses a button

- **WHEN** the binding clicks a button whose handler sets an FSM state
- **THEN** the callback query is from the user, and the state is under the user's key, not
  the binding's

### Requirement: A withheld trigger reports itself

A withheld trigger SHALL return `Withheld`, carrying the reason, which names `deliver=False`
when the test withheld it, and the withheld update, bound to the bot as one fed is, except
`create_topic()`, which SHALL return the new topic. The trigger SHALL open a route scope of its
own, left empty, so `routes` and `last_route` do not report the trigger before it and
`assert_updates_handled()` has nothing to flag.

#### Scenario: A withheld trigger after a handled one

- **WHEN** a handled trigger is followed by one with `deliver=False`
- **THEN** `routes` is empty, `last_route` is `None`, and `assert_updates_handled()` passes

#### Scenario: A withheld callback query is answerable

- **WHEN** a user clicks a button with `deliver=False`
- **THEN** `answer()` on the returned update's `callback_query` succeeds

#### Scenario: A withheld topic

- **WHEN** a user creates a topic with `deliver=False`
- **THEN** the trigger returns the new topic, and nothing is fed

### Requirement: Only successful modeled sends count toward a flood limit

The counted methods SHALL be the modeled sends, read off the modeling registry. A call SHALL
be counted once it succeeds, as every message it puts into the chat: a media group or batch of
ten counts ten. A call SHALL be let through while the chat is under a limit, and MAY take it
over. The limits SHALL be read off the event loop's clock plus the time `advance_time` moved.

#### Scenario: A media group counts every message

- **WHEN** the bot sends two media groups of ten into a group
- **THEN** a third raises `TelegramRetryAfter`, and the first two were not refused

#### Scenario: A refused call is not counted

- **WHEN** a call is refused
- **THEN** it does not count toward the limit and changes nothing

#### Scenario: Advancing the time lifts the limit

- **WHEN** a test moves the clock with `advance_time` past the window
- **THEN** the limit is read off the event loop's clock plus that advance
