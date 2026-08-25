## 1. The ledger

- [x] 1.1 Add `StarTransactionState` and `StarLedger` with a declared opening balance; derive the balance from transactions, never store it (design D1)
- [x] 1.2 Add `Blueprint` declaration for the starting balance
- [x] 1.3 Model `GetMyStarBalance` and `GetStarTransactions`
- [x] 1.4 Tests: balance equals opening balance plus transactions after arbitrary sequences; declared balance readable with no payment

## 2. Charges

- [x] 2.1 Record a charge from `actor.pay(...)` — id, payer, amount, subscription flag — and carry its id on the `successful_payment` message (design D2)
- [x] 2.2 Credit the ledger when a payment is recorded
- [x] 2.3 Tests: a payment credits the balance and appears in the transactions

## 3. Refunds and subscriptions

- [x] 3.1 Model `RefundStarPayment` against the recorded charge, debiting the ledger and flagging the charge (design D3)
- [x] 3.2 Model `EditUserStarSubscription` against the same charge
- [x] 3.3 Raise `TelegramBadRequest` for an unknown charge and for an already-refunded one
- [x] 3.4 Tests: pay then refund restores the balance; double refund fails; fabricated charge fails; cancel and re-enable round-trip

## 4. Gift inventory

- [x] 4.1 Add `OwnedGiftState` and `World.owned_gifts` keyed by owned id, with the owner as a field (design D4)
- [x] 4.2 Add the fixed gift catalogue and model `GetAvailableGifts` (design D5)
- [x] 4.3 Add `Blueprint` declaration for gifts already owned
- [x] 4.4 Tests: catalogue is stable across calls; declared gifts are readable

## 5. Gift methods

- [x] 5.1 Model `SendGift` — create owned inventory, spend from the ledger, allowing a negative balance (design D6)
- [x] 5.2 Model `GetUserGifts`, `GetChatGifts` and `GetBusinessAccountGifts` as filters over the inventory
- [x] 5.3 Model `ConvertGiftToStars`, `UpgradeGift` and `TransferGift`
- [x] 5.4 Model `GetBusinessAccountStarBalance` and `TransferBusinessAccountStars`
- [x] 5.5 Model `GiftPremiumSubscription` as a ledger spend
- [x] 5.6 Raise `TelegramBadRequest` for an unknown `owned_gift_id`
- [x] 5.7 Tests per method: inventory after, balance after, and the unknown-gift error

## 6. Non-enforcement

- [x] 6.1 Assert that a gift operation on a connection lacking the right still succeeds, consistent with the toolkit's stance
- [x] 6.2 Test: an insufficient balance drives the balance negative rather than raising (design D6)

## 7. Documentation

- [x] 7.1 Add a "Stars and gifts" section to `docs/dispatcher/testing.rst`
- [x] 7.2 Show pay → read the charge id → refund, since that is the flow the cluster exists for
- [x] 7.3 State the non-goals: no rights enforcement, no affordability check, no commission or payout modeling, and a fake gift catalogue
- [x] 7.4 Build docs and fix any new warnings

## 8. Release readiness

- [x] 8.1 No new fragment: the toolkit is unreleased, so this folded into its existing `CHANGES/1874.feature.rst` entry
- [x] 8.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing` at 100%
- [x] 8.3 Confirm the synthesis guard over every generated return type still passes
- [x] 8.4 Removed the stars-and-gifts cluster from the deferred lists in `RECORD_ONLY`'s comment and in the docs
