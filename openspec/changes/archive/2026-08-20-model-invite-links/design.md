## Context

Six methods, one list. `createChatInviteLink` and `createChatSubscriptionInviteLink`
append; `editChatInviteLink` and `editChatSubscriptionInviteLink` mutate by URL;
`revokeChatInviteLink` marks revoked by URL; `exportChatInviteLink` replaces the primary
link. `getChat` — already modeled — should report the primary one.

The reason this is a change of its own rather than a few lines folded into
`model-chat-administration` is correlation. The value is not "a link is stored"; it is
that the URL a handler received from `createChatInviteLink` is the URL
`revokeChatInviteLink` later resolves. That requires a real registry keyed by URL, and a
URL generator whose output is stable and unique within an environment.

The Bot API pins two behaviors worth honoring exactly, both documented rather than
server-side folklore:

- `exportChatInviteLink` revokes any previously generated primary link.
- Revoking the primary link automatically generates a new one.

## Goals / Non-Goals

**Goals:**

- Correlation: create → store URL → edit/revoke that URL resolves the same link.
- A truthful `getChat().invite_link`.
- The two documented primary-link behaviors above.

**Non-Goals:**

- **Joining via a link.** No `member_limit` enforcement, no `pending_join_request_count`
  incrementing, no expiry by wall clock. A user actor joins a chat directly; links are not
  a route into membership. This is what keeps the cluster closed and free of half-modeled
  edges.
- Administrator-right checks (`can_invite_users`), consistent with the toolkit's
  permissions-are-not-enforced stance.
- Star payments for subscription links. The price is stored; no balance moves.

## Decisions

### D1. `InviteLinkState` list on `ChatState`, plus a primary pointer

```
InviteLinkState:
    invite_link: str
    creator_id: int
    name: str | None
    expire_date: datetime | None
    member_limit: int | None
    creates_join_request: bool
    subscription_period: int | None
    subscription_price: int | None
    is_primary: bool
    is_revoked: bool
```

`ChatState.invite_links: list[InviteLinkState]` with lookup by URL. `is_primary` on the
state rather than a separate pointer field keeps one source of truth and makes "the
primary link" a filter, not a reference that can dangle after a revoke.

### D2. Deterministic, unique URLs from the world counter

Links are `https://t.me/+<counter>`-shaped, drawn from the existing monotonic world
counter. Deterministic so tests can be written against them if they want to; unique so
correlation works; no randomness, consistent with the rest of the fake (and with the
prohibition on nondeterminism that makes the suite reproducible).

### D3. Edit and revoke return the stored object

`model_copy` of a synthesized `ChatInviteLink` would satisfy the type and defeat the
purpose. Handlers mutate `InviteLinkState` and convert to `ChatInviteLink` at the
boundary, exactly as the rest of the world model does for `Chat`, `User` and `Message`.

### D4. The documented primary-link behaviors are modeled; nothing else is

`exportChatInviteLink` marks the current primary revoked and appends a new primary.
Revoking a primary appends a replacement. Both are documented statements about the API's
own behavior, not about server policy, so modeling them is fidelity rather than guessing.

Everything else — link expiry, join-request queues, member limits — is policy and stays
out.

### D5. One validation, because it is documented as a constant

`subscription_period` must be `2592000`; the Bot API states it as a fixed value, not a
range. Rejecting anything else is a documented contract, catches a real mistake, and costs
one comparison. It is deliberately the only validation in the cluster.

### D6. Blueprint declares links

Consistent with topics, business connections and communities: a frozen declaration,
deep-copied by `Blueprint.build()`. Declared and API-created links must be
indistinguishable, which the shared materialization path guarantees.

## Risks / Trade-offs

- **Links look like they grant membership (Non-Goals)** → a reader assumes joining via a
  link with `member_limit=1` fails the second time. Mitigation: the docs section states
  that links are metadata only and that membership is driven by actors.
- **URL format is now observable** → a test could assert on the exact `t.me/+N` shape and
  break if the generator changes. Mitigation: the docs show correlating by the *returned*
  URL rather than by a literal, and no scenario in the spec pins the format.
- **The `is_primary` invariant** → two primaries, or none, after an unusual sequence.
  Mitigation: a single helper performs the "revoke current primary, append new primary"
  transition used by both `exportChatInviteLink` and the revoke path, with a test
  asserting exactly one active primary after each.
- **Cluster growth pressure** → the next reader wants join-by-link. Mitigation: the
  non-goal is explicit; if it is ever wanted it belongs with the membership triggers, not
  here.

## Migration Plan

Purely additive. A test today asserting on a synthesized `ChatInviteLink` field keeps
type-checking; it may see different values, which is the defect being fixed.

## Open Questions

- Should `getChat().invite_link` be `None` for a chat that never exported one, or should
  the environment mint a primary link lazily on first read? Leaning `None` — a chat with
  no primary link is a real state, and lazy minting would make a read mutate the world.
