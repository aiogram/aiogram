## Why

The toolkit can drive a payment end to end — shipping query, pre-checkout query, a
`successful_payment` message — but everything *after* the payment is unmodeled. A bot that
sells anything typically does three things the fake cannot currently support:

- checks its own Telegram Stars balance before promising something,
- refunds a charge, keyed by the `telegram_payment_charge_id` it was given,
- reads back its star transactions to reconcile.

`getMyStarBalance` returns a synthesized number, so a bot that branches on "can I afford
this?" takes an arbitrary branch. `refundStarPayment` accepts any charge id, including ones
that were never paid, so the double-refund bug — a real and expensive one — passes its
tests. This is the largest remaining cluster where record-only genuinely costs coverage,
and unlike the others it connects to a flow the toolkit already drives.

Gifts are the same shape: `sendGift` deducts stars and creates an owned gift,
`convertGiftToStars` turns one back, `transferGift` and `upgradeGift` move and spend. Their
own methods read the inventory back (`getUserGifts`, `getChatGifts`,
`getBusinessAccountGifts`), so the cluster is self-describing — and pointless one method at
a time, since every one of them either reads or writes the same two things.

## What Changes

- **A star ledger.** The bot has a balance, and every star movement is a recorded
  transaction: payments received through the existing `pay` trigger credit it, refunds
  debit it, gifts and upgrades spend from it. `getMyStarBalance` and `getStarTransactions`
  read that ledger.
- **Refunds are tied to real charges.** `refundStarPayment` resolves the
  `telegram_payment_charge_id` that `actor.pay(...)` minted, credits the user back, and
  fails on an unknown or already-refunded charge — the double-refund case.
- **Subscriptions are stateful.** `editUserStarSubscription` cancels or re-enables the
  subscription behind a charge, and the `subscription` trigger reflects it.
- **A gift inventory.** `sendGift` creates an owned gift for the recipient and spends the
  stars; `getUserGifts`, `getChatGifts` and `getBusinessAccountGifts` read it;
  `convertGiftToStars`, `upgradeGift` and `transferGift` move it. `getAvailableGifts`
  returns a stable catalogue a test can pick from deterministically.
- **A blueprint declares the starting balance and any gifts already owned**, so a test does
  not have to earn its stars first.
- **Rights are still not enforced** — `can_convert_gifts_to_stars` and friends are business
  bot rights, and the toolkit does not enforce rights anywhere.

**BREAKING for tests that refund a fabricated charge id**: those now raise. That is the
defect.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: stars and gifts become world state, with the payment flow the
  toolkit already drives feeding the ledger.

## Impact

- **Code**: `aiogram/test/world.py` (`StarLedger`, `OwnedGiftState`, catalogue),
  `blueprint.py` (starting balance, owned gifts), `actors.py` (`pay` records a charge),
  `modeling.py` (the ~15 methods).
- **Tests**: a new module under `tests/test_testing/`, holding the package at 100%.
- **Docs**: a "Stars and gifts" section in `docs/dispatcher/testing.rst`.
- **Depends on** the payment triggers from `complete-actor-triggers`, which is where charge
  ids come from.
- **Changelog**: `CHANGES/<issue-or-pr>.feature.rst`.
- **Risk**: the largest of the remaining clusters, and the one most able to drift from
  Telegram. Balance arithmetic is easy to get subtly wrong in a way tests then depend on,
  so the ledger derives the balance from its transactions rather than storing both.
