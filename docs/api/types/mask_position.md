# MaskPosition

## Description

This object describes the position on faces where a mask should be placed by default.


## Attributes

| Name | Type | Description |
| - | - | - |
| `point` | `#!python str` | The part of the face relative to which the mask should be placed. One of 'forehead', 'eyes', 'mouth', or 'chin'. |
| `x_shift` | `#!python float` | Shift by X-axis measured in widths of the mask scaled to the face size, from left to right. For example, choosing -1.0 will place mask just to the left of the default mask position. |
| `y_shift` | `#!python float` | Shift by Y-axis measured in heights of the mask scaled to the face size, from top to bottom. For example, 1.0 will place the mask just below the default mask position. |
| `scale` | `#!python float` | Mask scaling coefficient. For example, 2.0 means double size. |



## Location

- `from aiogram.types import MaskPosition`
- `from aiogram.api.types import MaskPosition`
- `from aiogram.api.types.mask_position import MaskPosition`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#maskposition)
