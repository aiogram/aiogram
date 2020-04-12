# Exceptions
This filters can be helpful for handling errors from the text messages.

## ExceptionTypeFilter

Allow to match exception by type

### Specification
| Argument | Type | Description |
| --- | --- | --- |
| `exception` |  `#!python3 Union[Type[Exception], Tuple[Type[Exception]]]` | Exception type(s) |


## ExceptionMessageFilter

Allow to match exception by message

### Specification
| Argument | Type | Description |
| --- | --- | --- |
| `match` |  `#!python3 Union[str, Pattern[str]]` | Regexp pattern |

## Allowed handlers

Allowed update types for this filters:

- `error`
