## MODIFIED Requirements

### Requirement: Fixture set and scopes

The plugin SHALL provide fixtures for the blueprint, the environment, the bot, the
dispatcher, the environment's default wait timeout, and convenience accessors for the
declared chats and users. The blueprint fixture SHALL be overridable at any scope, while the
environment and every object derived from it SHALL be function-scoped. The default wait
timeout fixture SHALL be overridable the same way as the blueprint and dispatcher fixtures,
and the environment fixture SHALL build the environment with the value it returns.

#### Scenario: Default fixtures work with no configuration

- **WHEN** a test requests the environment fixture without overriding anything
- **THEN** it receives an environment containing a default private chat, a default user,
  and a bot identity, ready to trigger events

#### Scenario: Project supplies its own dispatcher

- **WHEN** a project overrides the dispatcher fixture to return its real
  `Dispatcher` with all routers included
- **THEN** every environment dispatches into that configuration

#### Scenario: Project overrides the default wait timeout

- **WHEN** a project overrides the wait timeout fixture to return a shorter value
- **THEN** the environment fixture's `wait_for` and every chat and topic wait use that value
  by default, without the project reconstructing the environment fixture itself
