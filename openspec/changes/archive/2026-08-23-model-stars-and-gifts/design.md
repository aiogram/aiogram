## Context

`complete-actor-triggers` gave the toolkit a payment flow: `actor.shipping_query()`,
`actor.pre_checkout_query()`, `actor.pay()`, the last of which posts a `successful_payment`
message. That message carries a `telegram_payment_charge_id` — currently synthesized and
forgotten.

That forgotten id is the hinge of this change. `refundStarPayment` and
`editUserStarSubscription` both key on it, which means the star ledger is not a new island:
it is the missing second half of a flow already half-modeled. That is what distinguishes
this cluster from the other deferred ones, and why it is worth building while sticker sets
are not.

## Goals / Non-Goals

**Goals:**

- A balance a bot can branch on, and that matches what the bot was actually paid.
- Refunds that resolve a real charge, so double-refund is a failing test rather than a
  production incident.
- A gift inventory whose readers and writers agree.

**Non-Goals:**

- **Business bot rights.** `can_convert_gifts_to_stars`, `can_transfer_stars` and friends
  are not enforced — the toolkit enforces no rights anywhere, and reopening that here would
  make this cluster inconsistent with the rest.
- Telegram's star economics: commission, payout schedules, the 21-day hold, currency
  conversion. The ledger counts stars in and out; it does not model a business.
- Gift *upgrade* mechanics beyond ownership: a unique gift is an owned gift with a flag, not
  a modeled collectible with attributes and rarity.
- Paid reactions, which spend stars but belong to the reaction surface.

## Decisions

### D1. The balance is derived from transactions, never stored

`StarLedger.transactions: list[StarTransactionState]` plus a declared opening balance; the
balance is their sum. This is the same rule as poll counts and reaction counts, and for the
same reason: an aggregate stored beside its source drifts the first time a path updates one
and not the other. Money is the worst possible place to allow that drift, and a test suite
that depends on a drifted balance is worse than one with no balance at all.

*Alternative rejected:* an `int` balance mutated in place. Faster, and wrong the first time
a refund path forgets to decrement.

### D2. Charges are recorded by the payment trigger

`actor.pay(...)` records a charge — id, payer, amount, and whether it is a subscription —
and the `successful_payment` message carries that id. `refundStarPayment` and
`editUserStarSubscription` look it up.

This is what makes the cluster testable end to end rather than in isolation: a test pays,
reads the charge id off the message its handler received, and refunds *that*. No fabricated
identifiers anywhere, exactly as the query registry works for callback queries.

### D3. Refund and subscription state live on the charge

A charge carries `is_refunded` and `is_subscription_canceled` rather than there being
separate registries. Both methods are then a lookup plus a flag, and "already refunded" and
"unknown charge" collapse into one code path — the same shape the query registry uses.

### D4. Gifts are owned by a recipient, keyed by an owned id

`OwnedGiftState(owned_gift_id, gift_id, owner_id, is_unique)` in a single
`World.owned_gifts` mapping, with the owner as a field rather than a per-owner dict. The
readers differ only by which owner they filter on, and transfer becomes a field write
instead of a move between containers.

### D5. The catalogue is fixed data, not synthesis

`getAvailableGifts` returns a small hard-coded catalogue with stable ids and star costs.
Synthesizing it would make `gifts[0].id` differ between runs, and picking a gift from the
catalogue is the first thing any gift test does.

This is one of the few places the toolkit ships invented Bot API *data* rather than deriving
it. Justified because the alternative is nondeterminism in the most common path, and the
catalogue is documented as fake.

### D6. Spending does not check affordability

Sending a gift with an insufficient balance succeeds and drives the balance negative rather
than raising. Telegram would reject it, but affordability is policy, and a negative balance
is *visible* in a way a silent rejection is not — a test asserting on the balance sees the
problem immediately. Tests that want the rejection declare it with an override.

*This is the decision most likely to be revisited.* It is recorded here rather than left
implicit precisely because it is arguable.

## Risks / Trade-offs

- **Money arithmetic that tests come to depend on (D1)** → mitigated by deriving the
  balance and by a property-style test asserting balance equals the transaction sum after
  arbitrary sequences.
- **A negative balance looks like a bug in the fake (D6)** → mitigated by documenting it as
  deliberate and by the override recipe for the rejection case.
- **The cluster is large and its methods are individually shallow** → a lot of surface for
  the value. Mitigated by shipping it as one change: partial gift support is worse than
  none, since every reader and writer touches the same inventory.
- **Ships invented catalogue data (D5)** → could diverge from real gift ids. Accepted: the
  ids are documented as fake, and a test asserting on a *real* Telegram gift id was never
  going to be portable anyway.

## Migration Plan

Additive apart from refunds: a test refunding a fabricated charge id now raises, which is
the defect. Land after `complete-actor-triggers`, whose payment triggers this builds on.

## Open Questions

- Should `getStarTransactions` honour `offset` and `limit`? Modeling pagination for a list a
  test builds itself is probably wasted effort — leaning toward returning everything and
  documenting it, unless a real bot's pagination logic is the thing under test.
