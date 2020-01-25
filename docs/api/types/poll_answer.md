# PollAnswer

## Description

This object represents an answer of a user in a non-anonymous poll.


## Attributes

| Name | Type | Description |
| - | - | - |
| `poll_id` | `#!python str` | Unique poll identifier |
| `user` | `#!python User` | The user, who changed the answer to the poll |
| `option_ids` | `#!python List[int]` | 0-based identifiers of answer options, chosen by the user. May be empty if the user retracted their vote. |



## Location

- `from aiogram.types import PollAnswer`
- `from aiogram.api.types import PollAnswer`
- `from aiogram.api.types.poll_answer import PollAnswer`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#pollanswer)
- [aiogram.types.User](../types/user.md)
