# UserProfilePhotos

## Description

This object represent a user's profile pictures.


## Attributes

| Name | Type | Description |
| - | - | - |
| `total_count` | `#!python int` | Total number of profile pictures the target user has |
| `photos` | `#!python List[List[PhotoSize]]` | Requested profile pictures (in up to 4 sizes each) |



## Location

- `from aiogram.types import UserProfilePhotos`
- `from aiogram.api.types import UserProfilePhotos`
- `from aiogram.api.types.user_profile_photos import UserProfilePhotos`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#userprofilephotos)
- [aiogram.types.PhotoSize](../types/photo_size.md)
