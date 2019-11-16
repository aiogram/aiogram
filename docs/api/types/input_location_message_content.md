# InputLocationMessageContent

## Description

Represents the content of a location message to be sent as the result of an inline query.


## Attributes

| Name | Type | Description |
| - | - | - |
| `latitude` | `#!python float` | Latitude of the location in degrees |
| `longitude` | `#!python float` | Longitude of the location in degrees |
| `live_period` | `#!python Optional[int]` | Optional. Period in seconds for which the location can be updated, should be between 60 and 86400. |



## Location

- `from aiogram.types import InputLocationMessageContent`
- `from aiogram.api.types import InputLocationMessageContent`
- `from aiogram.api.types.input_location_message_content import InputLocationMessageContent`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inputlocationmessagecontent)
