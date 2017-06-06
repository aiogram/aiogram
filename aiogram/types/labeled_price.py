from .base import Serializable


class LabeledPrice(Serializable):
    """
    This object represents a portion of the price for goods or services.
    
    https://core.telegram.org/bots/api#labeledprice
    """
    def __init__(self, label, amount):
        self.label = label
        self.amount = amount
