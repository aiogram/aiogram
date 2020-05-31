from aiogram.utils.helper import Helper, Item


class ParseMode(Helper):
    """
    Parse mode

    Source: https://core.telegram.org/bots/api#formatting-options
    """

    HTML = Item("HTML")
    MARKDOWN = Item("Markdown")
    MARKDOWN_V2 = Item("MarkdownV2")
