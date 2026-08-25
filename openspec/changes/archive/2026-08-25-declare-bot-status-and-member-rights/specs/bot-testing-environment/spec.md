## ADDED Requirements

### Requirement: The bot's own standing in a chat is declarable

A blueprint SHALL be able to declare what status the bot itself holds in a group, supergroup or
channel, either through a `bot_status` argument of the `add_*` helper or by naming
`blueprint.bot` in that chat's `members`. Declaring it both ways SHALL be rejected rather than
resolved, so neither spelling can silently shadow the other. Absent any declaration the bot
SHALL be an ordinary member of every such chat.

#### Scenario: Declaring the bot as an administrator

- **WHEN** a blueprint declares a supergroup with `bot_status` set to administrator and a
  handler calls `getChatMember` for the bot's own id
- **THEN** the administrator status is reported, so a handler gating itself on its own standing
  takes the same branch it would in production

#### Scenario: The two spellings are equivalent

- **WHEN** the bot's status is declared through `members` instead
- **THEN** the same status is reported

#### Scenario: Declaring it twice is rejected

- **WHEN** a blueprint passes both `bot_status` and an explicit `members` entry for the bot
- **THEN** the declaration raises, including when the status passed is the default one

### Requirement: Membership rights and permissions are declared state

A member's administrator rights and a restricted member's permissions SHALL be part of the
declared and stored membership, not invented when the membership is read. A blueprint SHALL be
able to declare them for any member, the bot included; an administrator declared without rights
SHALL hold the ordinary administrator rights, and a restriction declared without permissions
SHALL deny everything. The toolkit SHALL expose a factory that builds the ordinary
administrator rights with named overrides, so the case a test cares about — an administrator
lacking one right — is a single declaration.

#### Scenario: The bot is declared to lack a right

- **WHEN** a blueprint declares the bot as an administrator whose rights deny message deletion,
  and a handler reads its own membership
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
the anonymity flag alone — SHALL keep the member an administrator. `restrictChatMember` SHALL
store the permissions it was given and clear any administrator rights the member held.

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

#### Scenario: A restriction is read back as it was set

- **WHEN** a handler restricts a member with a set of permissions
- **THEN** `getChatMember` reports those permissions

### Requirement: Rights are reported per chat type

A membership read SHALL report each administrator right the way the Bot API reports it for that
chat's type: a right the API does not report there SHALL come back unset however it was
declared or granted, and a right it does report SHALL come back as a plain boolean even when it
was never stated.

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
Telegram answers all four with, so a bot that moderates a list of users fails in the test rather
than only in production.

#### Scenario: Acting on the owner fails

- **WHEN** a handler bans, restricts, promotes or demotes the chat's creator
- **THEN** the call raises `TelegramBadRequest` reporting that the chat owner cannot be removed

#### Scenario: Banning first is not a way around the guard

- **WHEN** a handler bans the owner and then promotes them
- **THEN** the first call already fails, so the owner's standing is never lost
