## ADDED Requirements

### Requirement: A restriction is reported separately from presence

A restricted user SHALL be reported with `is_member` telling whether they are in the chat,
and SHALL count as a member only while they are. Restricting a user who is not in the chat
SHALL leave them absent. A restricted member who leaves or rejoins SHALL stay restricted,
with only `is_member` changing, in both membership reads and membership updates.

#### Scenario: Restricting an absent user

- **WHEN** a handler restricts a user who never joined the chat
- **THEN** `getChatMember` reports them restricted with `is_member` false, and
  `getChatMemberCount` does not count them

#### Scenario: A restricted member leaves

- **WHEN** a restricted member's actor leaves the chat
- **THEN** the `chat_member` update moves them from restricted with `is_member` true to
  restricted with `is_member` false, and the permissions are unchanged

#### Scenario: A restricted user rejoins

- **WHEN** that user's actor joins again
- **THEN** they are restricted with `is_member` true and the same permissions

### Requirement: Granting every permission lifts a restriction

`restrictChatMember` granting every permission SHALL lift the restriction. The user SHALL
become a member if present and left otherwise, with no stored permissions or end date.

#### Scenario: Lifting a present member's restriction

- **WHEN** a handler restricts a member and then restricts them again granting every
  permission
- **THEN** `getChatMember` reports a plain member

#### Scenario: Lifting an absent user's restriction

- **WHEN** a handler lifts the restriction of a user who is not in the chat
- **THEN** `getChatMember` reports them as having left

### Requirement: Restriction and ban end dates are reported as Telegram reports them

A restriction or ban with no end SHALL report `until_date` as the Unix epoch, which is `0`
on the wire. A change to any status other than restricted or banned SHALL clear the stored
end date. A ban in a basic group SHALL have no end, since the Bot API applies `until_date`
for supergroups and channels only.

#### Scenario: A permanent ban

- **WHEN** a handler bans a user without an end date
- **THEN** `getChatMember` reports `until_date` as the Unix epoch

#### Scenario: Unbanning clears the end date

- **WHEN** a handler bans a user until a date and then unbans them
- **THEN** the user reads as having left, with no restriction end carried into a later
  membership

#### Scenario: A basic-group ban has no end

- **WHEN** a handler bans a user in a basic group with an end date
- **THEN** `getChatMember` reports `until_date` as the Unix epoch

### Requirement: Unbanning honours `only_if_banned`

`unbanChatMember` SHALL leave the user absent and free to join, removing a present member as
the Bot API documents for the default. With `only_if_banned`, it SHALL act on a banned user
only and leave anyone else as they are.

#### Scenario: Unbanning removes a present member by default

- **WHEN** a handler unbans a user who is a member of the chat
- **THEN** the user reads as having left

#### Scenario: `only_if_banned` leaves a member alone

- **WHEN** a handler unbans a member of the chat with `only_if_banned`
- **THEN** the user is still a member
