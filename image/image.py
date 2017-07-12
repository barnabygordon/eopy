import numpy as np
from osgeo import gdal, osr
from shapely.geometry import Polygon

from image.geotransform import Geotransform


class Image:
    """ A generic class for dealing with GDAL images """
    def __init__(self, image_dataset: gdal.Dataset):
        self.image_dataset = image_dataset
        self.geotransform = Geotransform(self.image_dataset)

    @classmethod
    def load(cls, filepath: str):
        image_dataset = gdal.Open(filepath)
        return Image(image_dataset)

    @property
    def width(self) -> int:
        return self.image_dataset.RasterXSize

    @property
    def height(self) -> int:
        return self.image_dataset.RasterYSize

    @property
    def bounds(self) -> ([float], [float]):
        """ The boundary of the image as a polygon """
        x_max = self.width * self.geotransform.pixel_width
        y_min = self.height * self.geotransform.pixel_width
        x = [self.geotransform.upper_left_x, x_max, x_max,
             self.geotransform.upper_left_x, self.geotransform.upper_left_x]
        y = [self.geotransform.upper_left_y, self.geotransform.upper_left_y,
             y_min, y_min, self.geotransform.upper_left_y]

        return Polygon(zip(x, y))

    @property
    def band_count(self) -> int:
        """ Number of bands in the image """
        return self.image_dataset.RasterCount

    @property
    def pixels(self) -> np.ndarray:
        """ The pixels data as a ndarray """
        return self.image_dataset.ReadAsArray().transpose(1, 2, 0)

    @property
    def projection(self) -> str:
        """ The projection of the image as a WKT string """
        return self.image_dataset.GetProjection()

    @property
    def epsg(self) -> str:
        spatial_reference = osr.SpatialReference(wkt=self.projection)
        return spatial_reference.GetAttrValue("AUTHORITY", 1)

    def get_window(self, x: int, y: int, width: int) -> np.ndarray:
        """ A slice of the image across all bands """
        return self.image_dataset.ReadAsArray(x, y, width, width)
