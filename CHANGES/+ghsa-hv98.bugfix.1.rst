The webhook handlers now decode the request body as UTF-8 and ignore the charset of the request, which could select a slow codec.
Reported by the Anthropic OSS Scanner (ANT-2026-HL9BRR9S).
