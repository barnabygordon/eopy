from typing import Tuple

from eopy.tools import gis


class Geotransform:

    def __init__(self, upper_left_x: float, upper_left_y: float, pixel_width: float, pixel_height: float, rotation_x: float, rotation_y: float):

        self.upper_left_x = upper_left_x
        self.upper_left_y = upper_left_y
        self.pixel_width = pixel_width
        self.pixel_height = pixel_height
        self.rotation_x = rotation_x
        self.rotation_y = rotation_y

    def __repr__(self) -> str:
        return f'(ulx, uly): ({self.upper_left_x}, {self.upper_left_y}) | xdist: {self.pixel_width}'

    @classmethod
    def from_tuple(cls, geo_transform: Tuple) -> "Geotransform":

        return cls(
            upper_left_x=geo_transform[0], upper_left_y=geo_transform[3],
            pixel_width=geo_transform[1], pixel_height=abs(geo_transform[5]),
            rotation_x=geo_transform[2], rotation_y=geo_transform[4])

    @classmethod
    def empty(cls) -> "Geotransform":

        return cls(upper_left_x=0, upper_left_y=0, pixel_width=1, pixel_height=1, rotation_x=0, rotation_y=0)

    @property
    def tuple(self):

        return self.upper_left_x, self.pixel_width, \
               self.rotation_x, self.upper_left_y, \
               self.rotation_y, -self.pixel_height

    def scale(self, factor: int) -> "Geotransform":

        return Geotransform(
            self.upper_left_x, self.upper_left_y,
            self.pixel_width / factor, self.pixel_height / factor,
            self.rotation_x, self.rotation_y)

    def subset(self, x: int, y: int) -> "Geotransform":
        """ Slice geo_transform to new position """

        upper_left_x, upper_left_y = gis.pixel_to_world(x, y, self)

        return Geotransform(
            upper_left_x, upper_left_y,
            self.pixel_width, self.pixel_height,
            self.rotation_x, self.rotation_y)
