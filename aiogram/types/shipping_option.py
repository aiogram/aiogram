from .base import Serializable


class ShippingOption(Serializable):
    """
    This object represents one shipping option.
    
    https://core.telegram.org/bots/api#shippingoption
    """
    def __init__(self, id, title, prices):
        self.id = id
        self.title = title
        self.prices = prices
