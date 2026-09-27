## MODIFIED Requirements

### Requirement: Tests are isolated by construction

Each test SHALL receive a freshly materialized environment. No message, membership
change, pending join request, outstanding query, FSM state, override, or recorded call
from one test SHALL be observable in another, regardless of the scope at which the
blueprint is shared.

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

#### Scenario: Outstanding queries do not leak between tests

- **WHEN** one test triggers a callback query and never answers it, and a later test in
  the same module answers a query identifier with the same value
- **THEN** the later test's call raises `TelegramBadRequest`, because the earlier test's
  outstanding query is not visible to it
