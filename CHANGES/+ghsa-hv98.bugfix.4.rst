List fields of Telegram objects, including nested rich text arrays, now stop validation at the first invalid item instead of collecting one error per item, so a validation error reports only the first invalid item of a list. The minimum supported pydantic version is now 2.8.0.
Reported by the Anthropic OSS Scanner (ANT-2026-NM3LC5D1).
