

class Geotransform:
    """ A class for easy access to the GDAL geotransform tuple """
    def __init__(self, geotransform_tuple: tuple):
        self.tuple = geotransform_tuple
        self.upper_left_x = self.tuple[0]
        self.upper_left_y = self.tuple[3]
        self.pixel_width = self.tuple[1]
        self.pixel_height = self.tuple[5]
        self.rotation_x = self.tuple[2]
        self.rotation_y = self.tuple[4]

    def __repr__(self):
        return "(ulx, uly): ({}, {}) | xdist: {} ".format(self.upper_left_x, self.upper_left_y, self.pixel_width)
