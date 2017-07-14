

class Geotransform:
    """ A class for easy access to the GDAL geotransform tuple """
    def __init__(self, image_dataset):
        self.geotransform = image_dataset.GetGeoTransform()
        self.upper_left_x = self.geotransform[0]
        self.upper_left_y = self.geotransform[3]
        self.pixel_width = self.geotransform[1]
        self.pixel_height = self.geotransform[5]
        self.rotation_x = self.geotransform[2]
        self.rotation_y = self.geotransform[4]
