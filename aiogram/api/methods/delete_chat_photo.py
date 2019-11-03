from typing import Any, Dict, Union

from .base import Request, TelegramMethod


class DeleteChatPhoto(TelegramMethod[bool]):
    """
    Use this method to delete a chat photo. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.

    Source: https://core.telegram.org/bots/api#deletechatphoto
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format @channelusername)"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})
        files: Dict[str, Any] = {}
        return Request(method="deleteChatPhoto", data=data, files=files)
