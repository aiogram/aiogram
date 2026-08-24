## ADDED Requirements

### Requirement: File content is declarable world state

The environment SHALL be able to hold the content of a file by its identifier, declared on
a blueprint, and SHALL serve that content to the framework's download helpers. `getFile`
SHALL report a size consistent with the content the environment holds.

#### Scenario: A declared file downloads its content

- **WHEN** a blueprint declares content for a file identifier and a handler downloads that
  file
- **THEN** the downloaded bytes are the declared content

#### Scenario: File size matches the content

- **WHEN** a handler calls `getFile` for an identifier the environment holds content for
- **THEN** the returned `File` reports the size of that content

#### Scenario: Declared content is isolated between environments

- **WHEN** two environments are built from one blueprint
- **THEN** content registered during one test is not visible to the other

### Requirement: Uploaded content is readable back

When a handler sends a file whose input carries its bytes directly, the environment SHALL
store those bytes against the resulting message's file identifier, so a bot that uploads
and then downloads within one test reads back what it sent.

#### Scenario: Round-tripping an uploaded document

- **WHEN** a handler sends a document built from an in-memory buffer and then downloads the
  file identifier from the stored message
- **THEN** the downloaded bytes are the bytes that were sent

### Requirement: Downloading content the environment does not have fails loudly

Downloading a file the environment holds no content for SHALL raise an error naming the
file and the ways to proceed, rather than yielding empty content. A testing tool must not
answer a question it cannot answer with a value that looks like an answer.

#### Scenario: An undeclared download raises

- **WHEN** a handler downloads a file whose content was never declared or uploaded
- **THEN** the call raises an error naming the file identifier and mentioning both
  declaring content and overriding the call

#### Scenario: The error is not silently swallowed by the download helpers

- **WHEN** the failure occurs inside `bot.download` or `bot.download_file`
- **THEN** the error surfaces to the test rather than leaving an empty destination
