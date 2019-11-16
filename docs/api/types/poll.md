# Poll

## Description

This object contains information about a poll.


## Attributes

| Name | Type | Description |
| - | - | - |
| `id` | `#!python str` | Unique poll identifier |
| `question` | `#!python str` | Poll question, 1-255 characters |
| `options` | `#!python List[PollOption]` | List of poll options |
| `is_closed` | `#!python bool` | True, if the poll is closed |



## Location

- `from aiogram.types import Poll`
- `from aiogram.api.types import Poll`
- `from aiogram.api.types.poll import Poll`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#poll)
- [aiogram.types.PollOption](../types/poll_option.md)
