from typing import Tuple

from remotesensing.tools import gis


class Geotransform:

    def __init__(self, geotransform: Tuple):

        self.upper_left_x = geotransform[0]
        self.upper_left_y = geotransform[3]
        self.pixel_width = geotransform[1]
        self.pixel_height = geotransform[5]
        self.rotation_x = geotransform[2]
        self.rotation_y = geotransform[4]

    def __repr__(self) -> str:
        return f'(ulx, uly): ({self.upper_left_x}, {self.upper_left_y}) | xdist: {self.pixel_width}'

    @property
    def tuple(self):

        return self.upper_left_x, self.pixel_width, self.rotation_x, self.upper_left_y, self.rotation_y, self.pixel_height

    def translate(self, x: int, y: int) -> "Geotransform":

        return Geotransform((x, self.pixel_width, self.rotation_x, y, self.rotation_y, self.pixel_height))

    def scale(self, factor: int) -> "Geotransform":

        return Geotransform((self.upper_left_x, self.pixel_width // factor, self.rotation_x,
                             self.upper_left_y, self.rotation_y, self.pixel_height // factor))

    def subset(self, x: int, y: int) -> "Geotransform":
        """ Slice geotransform to new position """

        upper_left_x, upper_left_y = gis.pixel_to_world(x, y, self)
        return Geotransform((upper_left_y, self.pixel_width, self.rotation_x, upper_left_x, self.rotation_y, self.pixel_height))
