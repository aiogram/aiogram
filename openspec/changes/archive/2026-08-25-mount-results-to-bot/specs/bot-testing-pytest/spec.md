## MODIFIED Requirements

### Requirement: Readable failure output

Assertion failures involving world state or recorded calls SHALL produce output that
identifies the relevant chat, message or method call, rather than an opaque object
`repr`. The plugin SHALL contribute pytest assertion representations for its own types.

Because an object the environment hands out carries a bot and an object built inside a test
does not, two such objects with identical payloads are unequal while printing identically. The
plugin SHALL recognize that comparison and say so, naming the binding on each side and the
comparison that does work. The explanation SHALL never itself fail: a comparison the plugin
cannot describe SHALL be left to pytest's own reporting, since the hook runs on every failing
`==` in any project that installs aiogram.

#### Scenario: Failed assertion on chat contents

- **WHEN** an assertion about the last message in a chat fails
- **THEN** the failure output shows the chat, the messages it contains, and the mismatch

#### Scenario: Failed assertion on a recorded call

- **WHEN** an assertion about a recorded API call fails
- **THEN** the failure output names the method and shows the fields that differ

#### Scenario: Two objects that differ only in their binding

- **WHEN** a test compares an object the environment returned against an identical one it
  built itself, and the comparison fails
- **THEN** the output states that the two differ only in the bot they are bound to, and points
  at comparing the payload instead

#### Scenario: An object the plugin cannot describe is left alone

- **WHEN** a failing comparison involves objects the plugin cannot serialize
- **THEN** no explanation is contributed and pytest's own failure report is what the user sees
