# MessageHandler

There is base class for message handlers.

## Simple usage:
```pyhton3
from aiogram.handlers import MessageHandler

...

@router.message_handler()
class MyTestMessageHandler(MessageHandler):
    filters = [Text(text="test")]

    async def handle() -> Any:
        return SendMessage(chat_id=self.chat.id, text="PASS")

```

## Extension

This base handler is subclass of [BaseHandler](basics.md#basehandler) with some extensions:

- `self.chat` is alias for `self.event.chat`
- `self.from_user` is alias for `self.event.from_user`
