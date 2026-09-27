## ADDED Requirements

### Requirement: Plugin registers itself with pytest

The toolkit SHALL register a pytest plugin through a `pytest11` entry point so that its
fixtures are available in any project that installs the testing extra, with no
`conftest.py` boilerplate. Installing the extra SHALL be the only setup step.

#### Scenario: Fixtures available without conftest

- **WHEN** a project installs `aiogram[test]` and writes a test that requests the
  environment fixture
- **THEN** the fixture resolves without the project declaring or importing any plugin

#### Scenario: Importing aiogram never requires pytest

- **WHEN** an application imports `aiogram` in an environment where pytest is not installed
- **THEN** the import succeeds, because the plugin module is imported only by pytest

### Requirement: Fixture set and scopes

The plugin SHALL provide fixtures for the blueprint, the environment, the bot, the
dispatcher, and convenience accessors for the declared chats and users. The blueprint
fixture SHALL be overridable at any scope, while the environment and every object derived
from it SHALL be function-scoped.

#### Scenario: Default fixtures work with no configuration

- **WHEN** a test requests the environment fixture without overriding anything
- **THEN** it receives an environment containing a default private chat, a default user,
  and a bot identity, ready to trigger events

#### Scenario: Project supplies its own dispatcher

- **WHEN** a project overrides the dispatcher fixture to return its real
  `Dispatcher` with all routers included
- **THEN** every environment dispatches into that configuration

#### Scenario: Blueprint shared at module or session scope

- **WHEN** a project overrides the blueprint fixture with a wider scope to describe a
  fixed cast of chats and users
- **THEN** all tests in that scope build environments from it, and the blueprint is
  constructed only once

### Requirement: Tests are isolated by construction

Each test SHALL receive a freshly materialized environment. No message, membership
change, FSM state, override, or recorded call from one test SHALL be observable in
another, regardless of the scope at which the blueprint is shared.

#### Scenario: State does not leak between tests

- **WHEN** one test sends messages, changes member statuses and sets FSM state, and a
  later test in the same module inspects the world
- **THEN** the later test sees the blueprint's initial state and an empty call log

#### Scenario: Isolation holds with a session-scoped blueprint

- **WHEN** the blueprint fixture is session-scoped and many tests mutate their environments
- **THEN** no test observes another test's mutations

#### Scenario: Environment is disposed after each test

- **WHEN** a test completes, whether it passed or failed
- **THEN** the environment's bot session and FSM storage are closed, leaving no pending
  tasks or open resources that would surface as warnings

### Requirement: Readable failure output

Assertion failures involving world state or recorded calls SHALL produce output that
identifies the relevant chat, message or method call, rather than an opaque object
`repr`. The plugin SHALL contribute pytest assertion representations for its own types.

#### Scenario: Failed assertion on chat contents

- **WHEN** an assertion about the last message in a chat fails
- **THEN** the failure output shows the chat, the messages it contains, and the mismatch

#### Scenario: Failed assertion on a recorded call

- **WHEN** an assertion about a recorded API call fails
- **THEN** the failure output names the method and shows the fields that differ

### Requirement: Usable without the plugin

Every capability exposed through fixtures SHALL also be reachable through public imports,
so projects that prefer their own fixtures, or that use a different test runner
arrangement, can construct blueprints and environments directly.

#### Scenario: Manual construction in a project's own fixture

- **WHEN** a project builds a blueprint and an environment inside its own fixture and
  disposes of it explicitly
- **THEN** the behavior is identical to using the provided fixtures

### Requirement: Async test configuration is the project's own

The plugin SHALL NOT impose an asyncio integration or an event loop policy; it SHALL work
with the project's existing async pytest setup. The documentation SHALL state the required
configuration.

#### Scenario: Project already configures async tests

- **WHEN** a project runs async tests through its chosen asyncio plugin and configuration
- **THEN** the toolkit's fixtures work without additional settings and without conflicting
  with that plugin
