## ADDED Requirements

### Requirement: The bot's star balance is a ledger

The environment SHALL record every movement of Telegram Stars as a transaction, and SHALL
derive the bot's balance from those transactions rather than storing it separately. A
blueprint SHALL be able to declare a starting balance. `getMyStarBalance` and
`getStarTransactions` SHALL read that ledger.

#### Scenario: A payment credits the balance

- **WHEN** a user actor completes a payment in stars
- **THEN** the bot's balance increases by the amount paid, and the transaction appears in
  `getStarTransactions`

#### Scenario: The balance always matches the transactions

- **WHEN** any sequence of payments, refunds and gift purchases has been applied
- **THEN** the reported balance equals the sum of the recorded transactions plus the
  declared starting balance

#### Scenario: A declared balance needs no payment first

- **WHEN** a blueprint declares a starting balance and a handler reads it
- **THEN** the declared amount is returned without any payment having been triggered

### Requirement: Refunds resolve a real charge

`refundStarPayment` SHALL resolve the `telegram_payment_charge_id` of a payment the
environment recorded, debit the bot's balance, and mark the charge refunded. Refunding an
unknown charge, or one already refunded, SHALL raise `TelegramBadRequest`.

#### Scenario: Refunding a payment the bot received

- **WHEN** a user actor pays and the handler refunds the charge id from the resulting
  message
- **THEN** the refund succeeds and the bot's balance returns to what it was before the
  payment

#### Scenario: Refunding twice fails

- **WHEN** a handler refunds the same charge a second time
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Refunding a charge that never existed fails

- **WHEN** a handler refunds a fabricated charge id
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Star subscriptions can be cancelled and re-enabled

`editUserStarSubscription` SHALL act on the subscription behind a recorded charge, and the
environment SHALL reflect whether that subscription is cancelled.

#### Scenario: Cancelling a subscription

- **WHEN** a handler cancels the subscription behind a charge it received
- **THEN** the environment reports that subscription as cancelled, and re-enabling it
  reverses that

#### Scenario: Acting on an unknown subscription fails

- **WHEN** a handler cancels a subscription for a charge the environment does not know
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Gifts are owned inventory

`sendGift` SHALL create an owned gift for its recipient and spend its cost from the bot's
balance. `getUserGifts`, `getChatGifts` and `getBusinessAccountGifts` SHALL read that
inventory, and `convertGiftToStars`, `upgradeGift` and `transferGift` SHALL move it.
`getAvailableGifts` SHALL return a stable catalogue.

#### Scenario: Sending a gift creates owned inventory

- **WHEN** a handler sends a gift to a user
- **THEN** that gift appears in the user's owned gifts, and the bot's balance falls by its
  cost

#### Scenario: The catalogue is stable

- **WHEN** a handler calls `getAvailableGifts` twice
- **THEN** the same gifts are returned in the same order, so a test can pick one
  deterministically

#### Scenario: Converting a gift returns its stars

- **WHEN** a handler converts an owned gift to stars
- **THEN** the gift leaves the inventory and the balance rises

#### Scenario: Transferring moves ownership

- **WHEN** a handler transfers an owned unique gift to another chat
- **THEN** the gift appears in the new owner's inventory and leaves the previous owner's

#### Scenario: Acting on a gift that is not owned fails

- **WHEN** a handler converts, upgrades or transfers an `owned_gift_id` the environment
  does not know
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Star rights are not enforced

The environment SHALL NOT enforce the business bot rights the Bot API requires for gift and
star operations, consistent with the toolkit not enforcing rights anywhere.

#### Scenario: A gift operation without the right still succeeds

- **WHEN** a handler converts a gift on a connection whose rights do not permit it
- **THEN** the call succeeds, and a test needing the rejection declares it with an override
