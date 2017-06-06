from .base import Deserializable


class ShippingAddress(Deserializable):
    """
    This object represents a shipping address.
    
    https://core.telegram.org/bots/api#shippingaddress
    """
    def __init__(self, country_code, state, city, street_line1, street_line2, post_code):
        self.country_code: str = country_code
        self.state: str = state
        self.city: str = city
        self.street_line1: str = street_line1
        self.street_line2: str = street_line2
        self.post_code: str = post_code

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        country_code = raw_data.get('country_code')
        state = raw_data.get('state')
        city = raw_data.get('city')
        street_line1 = raw_data.get('street_line1')
        street_line2 = raw_data.get('street_line2')
        post_code = raw_data.get('post_code')

        return ShippingAddress(country_code, state, city, street_line1, street_line2, post_code)
