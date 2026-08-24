## ADDED Requirements

### Requirement: Invite links are chat state

The environment SHALL store a chat's invite links, each carrying its URL, creator, name,
expiry, member limit, join-request flag, subscription period and price where applicable,
and whether it has been revoked. A blueprint SHALL be able to declare existing links, and
every environment built from it SHALL start from an independent copy.

#### Scenario: Declaring an existing link

- **WHEN** a blueprint declares an invite link on a chat and a handler edits it
- **THEN** the edit applies to the declared link without it having been created first

#### Scenario: Links are isolated between environments

- **WHEN** two environments are built from one blueprint and one of them revokes a
  declared link
- **THEN** the other environment still reports that link as active

### Requirement: Invite link methods act on stored links

`createChatInviteLink`, `createChatSubscriptionInviteLink`, `editChatInviteLink`,
`editChatSubscriptionInviteLink` and `revokeChatInviteLink` SHALL be applied to the chat's
stored links. Editing and revoking SHALL return the stored link, mutated — never a newly
synthesized object — so a link created earlier can be correlated with a later operation.

#### Scenario: Creating then revoking returns the same link

- **WHEN** a handler creates an invite link, stores its URL, and later revokes that URL
- **THEN** the revoked link returned is the one that was created, now marked revoked

#### Scenario: Editing mutates the stored link

- **WHEN** a handler edits an invite link's name and member limit
- **THEN** the returned link carries the new name and limit, and reading the chat's links
  shows the same values

#### Scenario: A subscription link keeps its subscription fields

- **WHEN** a handler creates a subscription invite link and then edits its name
- **THEN** the returned link keeps its subscription period and price, and carries the new
  name

#### Scenario: Acting on an unknown link fails

- **WHEN** a handler edits or revokes an invite link URL the chat does not have
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: An unsupported subscription period fails

- **WHEN** a handler creates a subscription invite link with a subscription period other
  than the value the Bot API permits
- **THEN** the call raises `TelegramBadRequest`

### Requirement: The primary invite link is reported by getChat

`exportChatInviteLink` SHALL replace the chat's primary invite link, revoking the previous
one and returning the new URL, and revoking the primary link SHALL generate a replacement
as Telegram does. The already-modeled `getChat` SHALL report the current primary link.

#### Scenario: Exporting replaces the primary link

- **WHEN** a handler calls `exportChatInviteLink` twice
- **THEN** the two returned URLs differ, the first is marked revoked, and `getChat`
  reports the second

#### Scenario: getChat reports the primary link

- **WHEN** a handler exports an invite link and then calls `getChat`
- **THEN** the chat's `invite_link` is the exported URL

#### Scenario: Revoking the primary link generates a replacement

- **WHEN** a handler revokes the chat's current primary link
- **THEN** the revoked link is returned marked revoked, and `getChat` reports a different,
  active primary link
