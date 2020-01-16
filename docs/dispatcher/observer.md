# Observer

Observer is used for filtering and handling different events. That is part of internal API with some public methods and is recommended to don't use methods is not listed here.

In `aiogram` framework is available two variants of observer:

1. [EventObserver](#eventobserver) 
1. [TelegramEventObserver](#telegrameventobserver)


## EventObserver
Reference: `#!python3 aiogram.dispatcher.event.observer.EventObserver`

That is base observer for all events.

### Base registering method
Method: `<observer>.register()`

| Argument | Type | Description |
| --- | --- | --- |
| `callback` | `#!python3 Callable[[Any], Awaitable[Any]]` | Event handler |

Will return original callback.


### Decorator-style registering method

Usage:
```python3
@<observer>()
async def handler(*args, **kwargs):
    pass
```

## TelegramEventObserver
Is subclass of [EventObserver](#eventobserver) with some differences.
Here you can register handler with filters or bounded filters which can be used as keyword arguments instead of writing full references when you register new handlers.
This observer will stops event propagation when first handler is pass.

### Registering bound filters

Bound filter should be subclass of [BaseFilter](filters/index.md)

`#!python3 <observer>.bind_filter(MyFilter)`

### Registering handlers
Method: `TelegramEventObserver.register(callback, filter1, filter2, ..., bound_filter=value, ...)`
In this method is added bound filters keywords interface.

| Argument | Type | Description |
| --- | --- | --- |
| `callback` | `#!python3 Callable[[Any], Awaitable[Any]]` | Event handler |
| `*filters` | `#!python3 Union[Callable[[Any], Any], Callable[[Any], Awaitable[Any]], BaseFilter]` | Ordered filters set |
| `**bound_filters` | `#!python3 Any` | Bound filters |


### Decorator-style registering event handler with filters

Usage:
```python3
@<observer>(filter1, filter2, ...)
async def handler(*args, **kwargs):
    pass
```
