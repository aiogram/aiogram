## 1. Send family

- [x] 1.1 Add `SendInvoice`, `SendGame`, `SendPaidMedia`, `SendChecklist`, `SendLivePhoto` and `SendRichMessage` to `MEDIA_FIELDS` with their `Message` payload fields (design D1)
- [x] 1.2 Verify each inherits reply resolution, topic threading, business attribution and `Default` resolution from `handle_send` without a per-method handler
- [x] 1.3 Tests: each method appends a `Message` carrying its payload field, with a unique `message_id`, and returns the stored message
- [x] 1.4 Test: an inline keyboard on a sent invoice and on a sent rich message is resolvable by `actor.click()`

## 2. Edit family completion

- [x] 2.1 Add the `InputMedia*`/`InputChecklist` → (`Message` field, type) mapping table (design D2)
- [x] 2.2 Model `EditMessageMedia` on top of `_edit_target` + `ChatState.update_message`, seeding the media object from the input's `media`, `caption` and `parse_mode`
- [x] 2.3 Model `EditMessageLiveLocation` (rebuild `Message.location`) and `EditMessageChecklist`
- [x] 2.4 Model `StopMessageLiveLocation` to return the stored message with `live_period` cleared (design D4)
- [x] 2.5 Raise `TelegramBadRequest` from all four when the target is unknown or deleted, and for inline-message targets, matching the existing text and caption edits
- [x] 2.6 Tests per method: mutated stored message, no extra message added, and the error path
- [x] 2.7 Parametrized guard test over every `InputMedia` union member asserting the mapping resolves (risk mitigation for D2)

## 2b. Sent payloads carry request values

- [x] 2b.1 Seed a synthesized payload with the values the request carried, matched by name and guarded by `annotation_accepts` (design D7)
- [x] 2b.2 Promote `annotation_accepts` out of the private namespace, since it is now used across modules
- [x] 2b.3 Tests: location coordinates and live period, contact details, video dimensions, paid-media star count
- [x] 2b.4 Test: a request field sharing a name with a differently-typed payload field is left alone (`sendVideo.cover`)

## 3. Batch forward and copy

- [x] 3.1 Model `ForwardMessages` and `CopyMessages` by delegating per id to the existing single-message handlers (design D3)
- [x] 3.1b Set `forward_origin` in the shared forward path, so a forward is distinguishable from a copy in the world at all (design D8)
- [x] 3.2 Skip individually-missing ids; raise `TelegramBadRequest` only for an unknown source chat
- [x] 3.3 Tests: batch forward carries forward origin, batch copy does not, returned ids exist in the target chat, unknown source chat fails, partially-missing ids return a shorter list

## 4. Pinning completion

- [x] 4.1 Model `UnpinAllChatMessages` to clear `ChatState.pinned_message_ids`
- [x] 4.2 Test: pin two messages, unpin all, assert the chat reports no pins

## 5. Seeded results

- [x] 5.1 `SendChatAction`: resolve the chat (raising `TelegramBadRequest` when unknown) and return `True`
- [x] 5.2 `GetFile`: echo the requested `file_id` in the returned `File`
- [x] 5.3 `CreateInvoiceLink`: return a deterministic link derived from the world counter
- [x] 5.4 `GetUserPersonalChatMessages`: read the last `limit` messages from that user's private chat when the environment knows one
- [x] 5.5 Tests for each, including `sendChatAction` against an unknown chat

## 6. Documentation

- [x] 6.1 Extend the modeled-method list in `docs/dispatcher/testing.rst`
- [x] 6.2 State explicitly that `sendInvoice` stores a message but models no payment flow, and that the ephemeral/draft methods are record-only by design
- [x] 6.3 Build docs and fix any new warnings

## 7. Release readiness

- [x] 7.1 `CHANGES/<issue-or-pr>.feature.rst`, noting that tests asserting an empty chat after these calls will newly fail
- [x] 7.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing` at 100%
- [x] 7.3 Confirm the parametrized synthesis guard over every generated return type still passes, proving the unmodeled remainder still answers
