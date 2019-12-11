# ContentTypesFilter

Is useful for handling specific types of messages (For example separate text and stickers handlers).
This is always automatically adds to the filters list for message handlers.

Can be imported:

- `#!python3 from aiogram.dispatcher.filters.content_types import ContentTypesFilter`
- `#!python3 from aiogram.dispatcher.filters import ContentTypesFilter`
- `#!python3 from aiogram.filters import ContentTypesFilter`

Or used from filters factory by passing corresponding arguments to handler registration line

!!! warning "Please be patient!"
    If no one content type filter is specified the `["text"]` value is automatically will be used.


## Specification

| Argument | Type | Description |
| --- | --- | --- |
| `content_types` | `#!python3 Optional[List[str]]` | List of allowed content types |

## Usage

1. Single content type: `#!python3 ContentTypesFilter(content_types=["sticker"])`
1. Multiple content types: `#!python3 ContentTypesFilter(content_types=["sticker", "photo"])`
1. Recommended: With usage of `ContentType` helper: `#!python3 ContentTypesFilter(content_types=[ContentType.PHOTO])`
1. Any content type: `#!python3 ContentTypesFilter(content_types=[ContentType.ANY])`

## Allowed handlers

Allowed update types for this filter:

- `message`
- `edited_message`
- `channel_post`
- `edited_channel_post`
