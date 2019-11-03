from aiogram.utils.helper import OrderedHelper, Item, ListItem


class TestOrderedHelper:

    def test_items_are_ordered(self):
        class Helper(OrderedHelper):
            A = Item()
            D = Item()
            C = Item()
            B = Item()

        assert Helper.all() == ['A', 'D', 'C', 'B']

    def test_list_items_are_ordered(self):
        class Helper(OrderedHelper):
            A = ListItem()
            D = ListItem()
            C = ListItem()
            B = ListItem()

        assert Helper.all() == ['A', 'D', 'C', 'B']
