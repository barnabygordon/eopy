from image.geotransform import Geotransform
from tools import gis

import geopandas as gpd


class Superpixels:
    """ A class to segment an image into superpixels for classification """
    def __init__(self, superpixels: gpd.GeoDataFrame, geotransform: Geotransform, epsg: int):
        self.superpixels = superpixels
        self.geotransform = geotransform
        self.epsg = epsg

    def save(self, filename: str, driver: str='GeoJSON'):
        superpixels = self.superpixels.drop('geometry', axis=1)
        superpixels.to_file(filename, driver=driver)

    def project_to_geographic(self):
        self.superpixels['geographic'] = self.superpixels.geometry.apply(
            lambda x: gis.polygon_to_world(x, self.geotransform))
        self.superpixels = self.superpixels.set_geometry('geographic')
