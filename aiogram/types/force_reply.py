from .base import Serializable


class ForceReply(Serializable):
    """
    Upon receiving a message with this object, 
    Telegram clients will display a reply interface to the user 
    (act as if the user has selected the bot‘s message and tapped ’Reply'). 
     
    This can be extremely useful if you want to create user-friendly step-by-step 
    interfaces without having to sacrifice privacy mode.

    https://core.telegram.org/bots/api#forcereply
    """
    def __init__(self, selective=None):
        self.selective = selective

    def to_json(self):
        data = {'force_reply': True}
        if self.selective:
            data['selective'] = True
        return data
