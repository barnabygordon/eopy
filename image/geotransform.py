

class Geotransform:
    """ A class for easy access to the GDAL geotransform tuple """
    def __init__(self, geotransform_tuple):
        self.geotransform = geotransform_tuple
        self.upper_left_x = self.geotransform[0]
        self.upper_left_y = self.geotransform[3]
        self.pixel_width = self.geotransform[1]
        self.pixel_height = self.geotransform[5]
        self.rotation_x = self.geotransform[2]
        self.rotation_y = self.geotransform[4]

    def __repr__(self):
        return "(ulx, uly): ({}, {}) | xdist: {} ".format(self.upper_left_x, self.upper_left_y, self.pixel_width)
