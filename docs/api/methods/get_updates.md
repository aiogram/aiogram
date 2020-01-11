# getUpdates

## Description

Use this method to receive incoming updates using long polling (wiki). An Array of Update objects is returned.

Notes

1. This method will not work if an outgoing webhook is set up.

2. In order to avoid getting duplicate updates, recalculate offset after each server response.


## Arguments

| Name | Type | Description |
| - | - | - |
| `offset` | `#!python3 Optional[int]` | Optional. Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates. By default, updates starting with the earliest unconfirmed update are returned. An update is considered confirmed as soon as getUpdates is called with an offset higher than its update_id. The negative offset can be specified to retrieve updates starting from -offset update from the end of the updates queue. All previous updates will forgotten. |
| `limit` | `#!python3 Optional[int]` | Optional. Limits the number of updates to be retrieved. Values between 1—100 are accepted. Defaults to 100. |
| `timeout` | `#!python3 Optional[int]` | Optional. Timeout in seconds for long polling. Defaults to 0, i.e. usual short polling. Should be positive, short polling should be used for testing purposes only. |
| `allowed_updates` | `#!python3 Optional[List[str]]` | Optional. List the types of updates you want your bot to receive. For example, specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of these types. See Update for a complete list of available update types. Specify an empty list to receive all updates regardless of type (default). If not specified, the previous setting will be used. |



## Response

Type: `#!python3 List[Update]`

Description: An Array of Update objects is returned.


## Usage


### As bot method bot

```python3
result: List[Update] = await bot.get_updates(...)
```

### Method as object

Imports:

- `from aiogram.methods import GetUpdates`
- `from aiogram.api.methods import GetUpdates`
- `from aiogram.api.methods.get_updates import GetUpdates`

#### In handlers with current bot
```python3
result: List[Update] = await GetUpdates(...)
```

#### With specific bot
```python3
result: List[Update] = await bot(GetUpdates(...))
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getupdates)
- [aiogram.types.Update](../types/update.md)
