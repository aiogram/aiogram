:code:`MaybeInaccessibleMessageUnion` is now discriminated by :code:`date` (:code:`0` means :class:`aiogram.types.inaccessible_message.InaccessibleMessage`), so nested messages are validated once instead of once per member, which took time exponential in the nesting depth.
Reported by the Anthropic OSS Scanner (ANT-2026-IOHAUKLG).
