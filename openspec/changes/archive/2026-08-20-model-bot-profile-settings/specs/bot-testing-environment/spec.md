## ADDED Requirements

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
