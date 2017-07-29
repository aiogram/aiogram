from .base import Deserializable


class MaskPosition(Deserializable):
    """
    This object describes the position on faces where a mask should be placed by default.

    https://core.telegram.org/bots/api#maskposition
    """

    def __init__(self, point, x_shift, y_shift, zoom):
        self.point: str = point
        self.x_shift: float = x_shift
        self.y_shift: float = y_shift
        self.zoom: float = zoom

    @classmethod
    def de_json(cls, raw_data):
        point = raw_data.get('point')
        x_shift = raw_data.get('x_shift')
        y_shift = raw_data.get('y_shift')
        zoom = raw_data.get('zoom')

        return cls(point=point, x_shift=x_shift, y_shift=y_shift, zoom=zoom)
