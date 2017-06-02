from .base import Serializable


class LabeledPrice(Serializable):
    def __init__(self, label, amount):
        self.label = label
        self.amount = amount
