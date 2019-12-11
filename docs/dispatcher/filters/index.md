# Basics

Filters is needed for routing updates to the specific handler.
Searching of handler is always stops on first match set of filters are pass. 

`aiogram` has some builtin useful filters.

## Builtin filters

Here is list of builtin filters and event types where it can be used:

| Filter                                    | update | message | edited_message | channel_post | edited_channel_post | inline_query | chosen_inline_result | callback_query | shipping_query | pre_checkout_query | poll |
| ----------------------------------------- |:------:|:-------:|:--------------:|:------------:|:-------------------:|:------------:|:--------------------:|:--------------:|:--------------:|:------------------:|:----:|
| [Text](text.md)                           |        | +       | +              | +            | +                   | +            |                      | +              |                |                    | +    |
| [ContentTypesFilter](content_types.md)    |        | +       | +              | +            | +                   |              |                      |                |                |                    |      |
| [Command](command.md)                     |        | +       |                |              |                     |              |                      |                |                |                    |      |
|                                           |        |         |                |              |                     |              |                      |                |                |                    |      |


## Own filters specification

Filters can be:

- Asynchronous function (`#!python3 async def my_filter(*args, **kwargs): pass`)
- Synchronous function (`#!python3 def my_filter(*args, **kwargs): pass`)
- Anonymous function (`#!python3 lambda event: True`)
- Any awaitable object
- Subclass of `BaseFilter`

Filters should return bool or dict. 
If the dictionary is passed as result of filter - resulted data will be propagated to the next 
filters and handler as keywords arguments.

## Writing bound filters

If you want to register own filters like builtin filters you will need to write subclass 
of BaseFilter (`#!python3 from aiogram.filters import BaseFilter`) with overriding the `__call__` 
method and adding filter attributes.

BaseFilter is subclass of `pydantic.BaseModel` that's mean all subclasses of BaseFilter has 
the validators based on class attributes and custom validator.

For example if you need to make simple text filter:

```python3
from aiogram.filters import BaseFilter


class MyText(BaseFilter):
    my_text: str

    async def __call__(self, message: Message) -> bool:
        return message.text == self.my_text


router.message_handler.bind_filter(MyText)

@router.message_handler(my_text="hello")
async def my_handler(message: Message): ...
``` 

!!! info
    Bound filters is always recursive propagates to the nested routers.
