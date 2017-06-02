from .base import Serializable


class ShippingOption(Serializable):
    def __init__(self, id, title, prices):
        self.id = id
        self.title = title
        self.prices = prices
