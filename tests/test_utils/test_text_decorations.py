from aiogram.types import MessageEntity, MessageEntityType
from aiogram.utils import text_decorations


class TestTextDecorations:
  def test_unparse_entities_normal_text(self):
    assert text_decorations.markdown_decoration.unparse(
      "hi i'm bold and italic and still bold",
      entities=[
        MessageEntity(offset=3, length=34, type=MessageEntityType.BOLD),
        MessageEntity(offset=12, length=10, type=MessageEntityType.ITALIC),
      ]
    ) == "hi *i'm bold _\rand italic_\r and still bold*"

  def test_unparse_entities_emoji_text(self):
    """
    emoji is encoded as two chars in json
    """
    assert text_decorations.markdown_decoration.unparse(
      "🚀 i'm bold and italic and still bold",
      entities=[
        MessageEntity(offset=3, length=34, type=MessageEntityType.BOLD),
        MessageEntity(offset=12, length=10, type=MessageEntityType.ITALIC),
      ]
    ) == "🚀 *i'm bold _\rand italic_\r and still bold*"
