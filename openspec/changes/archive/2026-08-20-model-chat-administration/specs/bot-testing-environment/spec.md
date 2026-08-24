## ADDED Requirements

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
