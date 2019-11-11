from typing import Tuple


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

    def translate(self, x: int, y: int) -> "Geotransform":

        return Geotransform((x, self.rotation_x, self.pixel_height, y, self.rotation_y, self.pixel_height))
