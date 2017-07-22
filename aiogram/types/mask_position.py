from .base import Serializable


class MaskPosition(Serializable):
    """
    This object describes the position on faces where a mask should be placed by default.

    https://core.telegram.org/bots/api#maskposition
    """

    def __init__(self, point, x_shift, y_shift, zoom):
        self.point: str = point
        self.x_shift: float = x_shift
        self.y_shift: float = y_shift
        self.zoom: float = zoom
