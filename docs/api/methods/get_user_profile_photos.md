# getUserProfilePhotos

## Description

Use this method to get a list of profile pictures for a user. Returns a UserProfilePhotos object.


## Arguments

| Name | Type | Description |
| - | - | - |
| `user_id` | `#!python3 int` | Unique identifier of the target user |
| `offset` | `#!python3 Optional[int]` | Optional. Sequential number of the first photo to be returned. By default, all photos are returned. |
| `limit` | `#!python3 Optional[int]` | Optional. Limits the number of photos to be retrieved. Values between 1—100 are accepted. Defaults to 100. |



## Response

Type: `#!python3 UserProfilePhotos`

Description: Returns a UserProfilePhotos object.


## Usage


### As bot method bot

```python3
result: UserProfilePhotos = await bot.get_user_profile_photos(...)
```

### Method as object

Imports:

- `from aiogram.methods import GetUserProfilePhotos`
- `from aiogram.api.methods import GetUserProfilePhotos`
- `from aiogram.api.methods.get_user_profile_photos import GetUserProfilePhotos`


#### With specific bot
```python3
result: UserProfilePhotos = await bot.emit(GetUserProfilePhotos(...))
```

#### In handlers with current bot
```python3
result: UserProfilePhotos = await GetUserProfilePhotos(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getuserprofilephotos)
- [aiogram.types.UserProfilePhotos](../types/user_profile_photos.md)
