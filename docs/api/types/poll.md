# Poll

## Description

This object contains information about a poll.


## Attributes

| Name | Type | Description |
| - | - | - |
| `id` | `#!python str` | Unique poll identifier |
| `question` | `#!python str` | Poll question, 1-255 characters |
| `options` | `#!python List[PollOption]` | List of poll options |
| `total_voter_count` | `#!python int` | Total number of users that voted in the poll |
| `is_closed` | `#!python bool` | True, if the poll is closed |
| `is_anonymous` | `#!python bool` | True, if the poll is anonymous |
| `type` | `#!python str` | Poll type, currently can be 'regular' or 'quiz' |
| `allows_multiple_answers` | `#!python bool` | True, if the poll allows multiple answers |
| `correct_option_id` | `#!python Optional[int]` | Optional. 0-based identifier of the correct answer option. Available only for polls in the quiz mode, which are closed, or was sent (not forwarded) by the bot or to the private chat with the bot. |



## Location

- `from aiogram.types import Poll`
- `from aiogram.api.types import Poll`
- `from aiogram.api.types.poll import Poll`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#poll)
- [aiogram.types.PollOption](../types/poll_option.md)
