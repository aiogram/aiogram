# Text

Is useful for filtering text [Message](../../api/types/message.md), 
any [CallbackQuery](../../api/types/callback_query.md) with `data`, 
[InlineQuery](../../api/types/inline_query.md) or
[Poll](../../api/types/poll.md) question.

Can be imported:

- `#!python3 from aiogram.dispatcher.filters.text import Text`
- `#!python3 from aiogram.dispatcher.filters import Text`
- `#!python3 from aiogram.filters import Text`

Or used from filters factory by passing corresponding arguments to handler registration line


## Specification

| Argument | Type | Description |
| --- | --- | --- |
| `text` | `#!python3 Optional[Union[str, List[str], Set[str], Tuple[str]]]` | Text equals value or one of values |
| `text_contains` | `#!python3 Optional[Union[str, List[str], Set[str], Tuple[str]]]` | Text contains value or one of values |
| `text_startswith` | `#!python3 Optional[Union[str, List[str], Set[str], Tuple[str]]]` | Text starts with value or one of values |
| `text_endswith` | `#!python3 Optional[Union[str, List[str], Set[str], Tuple[str]]]` | Text ends with value or one of values |
| `text_ignore_case` | `#!python3 bool` | Ignore case when checks (Default: `#!python3 False`) |

!!! warning
    
    Only one of `text`, `text_contains`, `text_startswith` or `text_endswith` argument can be used at once.
    Any of that arguments can be string, list, set or tuple of strings.  

## Usage

1. Text equals with the specified value: `#!python3 Text(text="text")  # value == 'text'`
1. Text starts with the specified value: `#!python3 Text(text_startswith="text")  # value.startswith('text')`
1. Text ends with the specified value: `#!python3 Text(text_endswith="text")  # value.endswith('text')`
1. Text contains the specified value: `#!python3 Text(text_endswith="text")  # value in 'text'`
1. Any of previous listed filters can be list, set or tuple of strings that's mean any of listed value should be equals/startswith/endswith/contains: `#!python3 Text(text=["text", "spam"])`
1. Ignore case can be combined with any previous listed filter: `#!python3 Text(text="Text", text_ignore_case=True)  # value.lower() == 'text'.lower()`

## Allowed handlers

Allowed update types for this filter:

- `message`
- `edited_message`
- `channel_post`
- `edited_channel_post`
- `inline_query`
- `callback_query`
