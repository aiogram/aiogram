# MessageHandler

There is base class for message handlers.

## Simple usage:
```pyhton3
from aiogram.handlers import MessageHandler

...

@router.message()
class MyHandler(MessageHandler):
    async def handle(self) -> Any:
        return SendMessage(chat_id=self.chat.id, text="PASS")

```

## Extension

This base handler is subclass of [BaseHandler](basics.md#basehandler) with some extensions:

- `self.chat` is alias for `self.event.chat`
- `self.from_user` is alias for `self.event.from_user`

## Related pages

- [BaseHandler](basics.md#basehandler)
- [Message](../../api/types/message.md)
- [Router.message](../router.md#message)
- [Router.edited_message](../router.md#edited-message)
- [Router.channel_post](../router.md#channel-post)
- [Router.edited_channel_post](../router.md#edited-channel-post)
