

class Geotransform:
    """ A class for easy access to the GDAL geotransform tuple """
    def __init__(self, upper_left_x, upper_left_y, pixel_width, pixel_height, rotation_x, rotation_y):
        """
        :type upper_left_x: float
        :type upper_left_y: float
        :type pixel_width: float
        :type pixel_height: float
        :type rotation_x: float
        :type rotation_y: float
        """

        self._upper_left_x = upper_left_x
        self._upper_left_y = upper_left_y
        self._pixel_width = pixel_width
        self._pixel_height = pixel_height
        self._rotation_x = rotation_x
        self._rotation_y = rotation_y

    @property
    def upper_left_x(self):
        return self._upper_left_x

    @property
    def upper_left_y(self):
        return self._upper_left_y

    @property
    def pixel_width(self):
        return self._pixel_width

    @property
    def pixel_height(self):
        return self._pixel_height

    @property
    def rotation_x(self):
        return self._rotation_x

    @property
    def rotation_y(self):
        return self._rotation_y

    def __repr__(self):
        return "(ulx, uly): ({}, {}) | xdist: {} ".format(self.upper_left_x, self.upper_left_y, self.pixel_width)
