## MODIFIED Requirements

### Requirement: Object shortcuts

Telegram objects SHALL expose ergonomic shortcuts that prefill ids from the
object itself.

A prefilled value that is derived by more than a plain attribute access SHALL be
produced by a named method on the object rather than by an expression inlined into
each generated shortcut, so that the rule has one definition and can be called
directly by users.

A shortcut SHALL only prefill a parameter that its target method declares.

#### Scenario: Message shortcuts

- **WHEN** `message.answer(...)`, `message.reply(...)`, `message.delete()` or `message.edit_text(...)` is called
- **THEN** `chat_id` / `message_id` are taken from the message

#### Scenario: Callback query shortcut

- **WHEN** `callback_query.answer(...)` is called
- **THEN** `callback_query_id` is filled automatically

#### Scenario: Reply parameters are built by a named method

- **WHEN** any `message.reply_*(...)` shortcut is called
- **THEN** `reply_parameters` is the result of `message.as_reply_parameters()`

#### Scenario: Ephemeral parameters are built by a named method

- **WHEN** a `message.reply_*(...)` shortcut whose method accepts `ephemeral_message_parameters` is called
- **THEN** that argument is the result of `message.as_ephemeral_message_parameters()`

#### Scenario: Shortcut does not prefill an undeclared parameter

- **WHEN** `message.reply_dice()`, `message.reply_poll(...)`, `message.reply_game(...)`, `message.reply_invoice(...)`, `message.reply_media_group(...)` or `message.reply_paid_media(...)` is called on an ephemeral message
- **THEN** the resulting method object carries no `ephemeral_message_parameters`, in its fields or in its extras

## ADDED Requirements

### Requirement: Ephemeral message parameters helper

`Message` SHALL expose `as_ephemeral_message_parameters()`, which builds the
`EphemeralMessageParameters` object describing who an ephemeral reply is addressed
to.

The helper SHALL accept `callback_query_id` and `replace_callback_query_message` as
optional keyword arguments, since neither value is derivable from a `Message`.

#### Scenario: Called on an ephemeral message

- **WHEN** `message.as_ephemeral_message_parameters()` is called and the message has an `ephemeral_message_id` and a sender
- **THEN** an `EphemeralMessageParameters` is returned whose `receiver_user_id` is the sender's id

#### Scenario: Called on a regular message

- **WHEN** `message.as_ephemeral_message_parameters()` is called and the message has no `ephemeral_message_id`
- **THEN** `None` is returned, so a shortcut that prefills it sends nothing

#### Scenario: Optional callback query fields

- **WHEN** `message.as_ephemeral_message_parameters(callback_query_id="q1", replace_callback_query_message=True)` is called on an ephemeral message
- **THEN** both values appear on the returned object
