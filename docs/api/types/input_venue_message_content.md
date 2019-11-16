# InputVenueMessageContent

## Description

Represents the content of a venue message to be sent as the result of an inline query.


## Attributes

| Name | Type | Description |
| - | - | - |
| `latitude` | `#!python float` | Latitude of the venue in degrees |
| `longitude` | `#!python float` | Longitude of the venue in degrees |
| `title` | `#!python str` | Name of the venue |
| `address` | `#!python str` | Address of the venue |
| `foursquare_id` | `#!python Optional[str]` | Optional. Foursquare identifier of the venue, if known |
| `foursquare_type` | `#!python Optional[str]` | Optional. Foursquare type of the venue, if known. (For example, 'arts_entertainment/default', 'arts_entertainment/aquarium' or 'food/icecream'.) |



## Location

- `from aiogram.types import InputVenueMessageContent`
- `from aiogram.api.types import InputVenueMessageContent`
- `from aiogram.api.types.input_venue_message_content import InputVenueMessageContent`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inputvenuemessagecontent)
