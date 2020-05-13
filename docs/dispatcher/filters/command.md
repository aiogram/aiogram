# Command

This filter can be helpful for handling commands from the text messages.

Works only with [Message](../../api/types/message.md) events which have the `text`.

## Specification
| Argument | Type | Description |
| --- | --- | --- |
| `commands` |  `#!python3 Union[Sequence[Union[str, re.Pattern]], Union[str, re.Pattern]]` | List of commands (string or compiled regexp patterns) |
| `commands_prefix` |  `#!python3 str` | Prefix for command. Prefix is always is single char but here you can pass all of allowed prefixes, for example: `"/!"` will work with commands prefixed by  `"/"` or `"!"` (Default: `"/"`). |
| `commands_ignore_case` |  `#!python3 bool` | Ignore case (Does not work with regexp, use flags instead. Default: `False`) |
| `commands_ignore_mention` |  `#!python3 bool` | Ignore bot mention. By default bot can not handle commands intended for other bots (Default: `False`) |


## Usage

1. Filter single variant of commands: `#!python3 Command(commands=["start"])` or `#!python3 Command(commands="start")`
1. Handle command by regexp pattern: `#!python3 Command(commands=[re.compile(r"item_(\d+)")])`
1. Match command by multiple variants: `#!python3 Command(commands=["item", re.compile(r"item_(\d+)")])`
1. Handle commands in public chats intended for other bots: `#!python3 Command(commands=["command"], commands)`
1. As keyword argument in registerer: `#!python3 @router.message(commands=["help"])`

!!! warning 
    Command cannot include spaces or any whitespace

## Allowed handlers

Allowed update types for this filter:

- `message`
- `edited_message`
