from aiogram.utils.helper import Item, ListItem, OrderedHelper


class TestOrderedHelper:
    @staticmethod
    def test_items_are_ordered():
        class Helper(OrderedHelper):
            A = Item()
            D = Item()
            C = Item()
            B = Item()

        if Helper.all() != ["A", "D", "C", "B"]:
            raise AssertionError

    @staticmethod
    def test_list_items_are_ordered():
        class Helper(OrderedHelper):
            A = ListItem()
            D = ListItem()
            C = ListItem()
            B = ListItem()

        if Helper.all() != ["A", "D", "C", "B"]:
            raise AssertionError
