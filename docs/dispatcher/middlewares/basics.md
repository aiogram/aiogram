# Basics



All middlewares should be made with `BaseMiddleware` (`#!python3 from aiogram import BaseMiddleware`) as base class.

For example:

```python3
class MyMiddleware(BaseMiddleware): ...
```

And then use next pattern in naming callback functions in middleware: `on_{step}_{event}`

Where is:

- `#!python3 step`:
    - `#!python3 pre_process`
    - `#!python3 process`
    - `#!python3 post_process`
- `#!python3 event`:
    - `#!python3 update`
    - `#!python3 message`
    - `#!python3 edited_message`
    - `#!python3 channel_post`
    - `#!python3 edited_channel_post`
    - `#!python3 inline_query`
    - `#!python3 chosen_inline_result`
    - `#!python3 callback_query`
    - `#!python3 shipping_query`
    - `#!python3 pre_checkout_query`
    - `#!python3 poll`
    - `#!python3 poll_answer`
    - `#!python3 error`

## Connecting middleware with router

Middlewares can be connected with router by next ways:

1. `#!python3 router.use(MyMiddleware())` (**recommended**)
1. `#!python3 router.middleware.setup(MyMiddleware())`
1. `#!python3 MyMiddleware().setup(router.middleware)` (**not recommended**)

!!! warning
    One instance of middleware **can't** be registered twice in single or many middleware managers

## The specification of step callbacks

### Pre-process step

| Argument | Type | Description |
| --- | --- | --- |
| event name | Any of event type (Update, Message and etc.) | Event |
| `#!python3 data` | `#!python3 Dict[str, Any]` | Contextual data (Will be mapped to handler arguments) |

Returns `#!python3 Any`

### Process step

| Argument | Type | Description |
| --- | --- | --- |
| event name | Any of event type (Update, Message and etc.) | Event |
| `#!python3 data` | `#!python3 Dict[str, Any]` | Contextual data (Will be mapped to handler arguments) |

Returns `#!python3 Any`

### Post-Process step

| Argument | Type | Description |
| --- | --- | --- |
| event name | Any of event type (Update, Message and etc.) | Event |
| `#!python3 data` | `#!python3 Dict[str, Any]` | Contextual data (Will be mapped to handler arguments) |
| `#!python3 result` | `#!python3 Dict[str, Any]` | Response from handlers |

Returns `#!python3 Any`

## Full list of available callbacks

- `#!python3 on_pre_process_update` - will be triggered on **pre process** `#!python3 update` event
- `#!python3 on_process_update` - will be triggered on **process** `#!python3 update` event
- `#!python3 on_post_process_update` - will be triggered on **post process** `#!python3 update` event
- `#!python3 on_pre_process_message` - will be triggered on **pre process** `#!python3 message` event
- `#!python3 on_process_message` - will be triggered on **process** `#!python3 message` event
- `#!python3 on_post_process_message` - will be triggered on **post process** `#!python3 message` event
- `#!python3 on_pre_process_edited_message` - will be triggered on **pre process** `#!python3 edited_message` event
- `#!python3 on_process_edited_message` - will be triggered on **process** `#!python3 edited_message` event
- `#!python3 on_post_process_edited_message` - will be triggered on **post process** `#!python3 edited_message` event
- `#!python3 on_pre_process_channel_post` - will be triggered on **pre process** `#!python3 channel_post` event
- `#!python3 on_process_channel_post` - will be triggered on **process** `#!python3 channel_post` event
- `#!python3 on_post_process_channel_post` - will be triggered on **post process** `#!python3 channel_post` event
- `#!python3 on_pre_process_edited_channel_post` - will be triggered on **pre process** `#!python3 edited_channel_post` event
- `#!python3 on_process_edited_channel_post` - will be triggered on **process** `#!python3 edited_channel_post` event
- `#!python3 on_post_process_edited_channel_post` - will be triggered on **post process** `#!python3 edited_channel_post` event
- `#!python3 on_pre_process_inline_query` - will be triggered on **pre process** `#!python3 inline_query` event
- `#!python3 on_process_inline_query` - will be triggered on **process** `#!python3 inline_query` event
- `#!python3 on_post_process_inline_query` - will be triggered on **post process** `#!python3 inline_query` event
- `#!python3 on_pre_process_chosen_inline_result` - will be triggered on **pre process** `#!python3 chosen_inline_result` event
- `#!python3 on_process_chosen_inline_result` - will be triggered on **process** `#!python3 chosen_inline_result` event
- `#!python3 on_post_process_chosen_inline_result` - will be triggered on **post process** `#!python3 chosen_inline_result` event
- `#!python3 on_pre_process_callback_query` - will be triggered on **pre process** `#!python3 callback_query` event
- `#!python3 on_process_callback_query` - will be triggered on **process** `#!python3 callback_query` event
- `#!python3 on_post_process_callback_query` - will be triggered on **post process** `#!python3 callback_query` event
- `#!python3 on_pre_process_shipping_query` - will be triggered on **pre process** `#!python3 shipping_query` event
- `#!python3 on_process_shipping_query` - will be triggered on **process** `#!python3 shipping_query` event
- `#!python3 on_post_process_shipping_query` - will be triggered on **post process** `#!python3 shipping_query` event
- `#!python3 on_pre_process_pre_checkout_query` - will be triggered on **pre process** `#!python3 pre_checkout_query` event
- `#!python3 on_process_pre_checkout_query` - will be triggered on **process** `#!python3 pre_checkout_query` event
- `#!python3 on_post_process_pre_checkout_query` - will be triggered on **post process** `#!python3 pre_checkout_query` event
- `#!python3 on_pre_process_poll` - will be triggered on **pre process** `#!python3 poll` event
- `#!python3 on_process_poll` - will be triggered on **process** `#!python3 poll` event
- `#!python3 on_post_process_poll` - will be triggered on **post process** `#!python3 poll` event
- `#!python3 on_pre_process_poll_answer` - will be triggered on **pre process** `#!python3 poll_answer` event
- `#!python3 on_process_poll_answer` - will be triggered on **process** `#!python3 poll_answer` event
- `#!python3 on_post_process_poll_answer` - will be triggered on **post process** `#!python3 poll_answer` event
- `#!python3 on_pre_process_error` - will be triggered on **pre process** `#!python3 error` event
- `#!python3 on_process_error` - will be triggered on **process** `#!python3 error` event
- `#!python3 on_post_process_error` - will be triggered on **post process** `#!python3 error` event
