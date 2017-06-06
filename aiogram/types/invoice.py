from .base import Deserializable


class Invoice(Deserializable):
    """
    This object contains basic information about an invoice.
    
    https://core.telegram.org/bots/api#invoice
    """
    def __init__(self, title, description, start_parameter, currency, total_amount):
        self.title: str = title
        self.description: str = description
        self.start_parameter: str = start_parameter
        self.currency: str = currency
        self.total_amount: int = total_amount

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        title = raw_data.get('title')
        description = raw_data.get('description')
        start_parameter = raw_data.get('start_parameter')
        currency = raw_data.get('currency')
        total_amount = raw_data.get('total_amount')

        return Invoice(title, description, start_parameter, currency, total_amount)
