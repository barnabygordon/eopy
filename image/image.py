import numpy as np
from osgeo import gdal, osr
from shapely.geometry import Polygon

from image.geotransform import Geotransform


class Image:
    """ A generic image object revolving around gdal """
    def __init__(self, image_dataset: gdal.Dataset):
        self.dataset = image_dataset
        self.geotransform = Geotransform(self.dataset)

    @classmethod
    def load(cls, filepath: str):
        image_dataset = gdal.Open(filepath)
        return Image(image_dataset)

    @property
    def width(self) -> int:
        return self.dataset.RasterXSize

    @property
    def height(self) -> int:
        return self.dataset.RasterYSize

    @property
    def bounds(self) -> Polygon:
        x_max = self.width * self.geotransform.pixel_width
        y_min = self.height * self.geotransform.pixel_width
        x = [self.geotransform.upper_left_x, x_max, x_max,
             self.geotransform.upper_left_x, self.geotransform.upper_left_x]
        y = [self.geotransform.upper_left_y, self.geotransform.upper_left_y,
             y_min, y_min, self.geotransform.upper_left_y]

        return Polygon(zip(x, y))

    @property
    def band_count(self) -> int:
        return self.dataset.RasterCount

    @property
    def pixels(self) -> np.ndarray:
        """ The pixels data as a ndarray """
        pixels = self.dataset.ReadAsArray()
        if self.band_count > 1:
            return pixels.transpose(1, 2, 0)
        else:
            return pixels

    @property
    def projection(self) -> str:
        """ The projection of the image as a WKT string """
        return self.dataset.GetProjection()

    @property
    def epsg(self) -> str:
        spatial_reference = osr.SpatialReference(wkt=self.projection)
        return spatial_reference.GetAttrValue("AUTHORITY", 1)

    def get_window(self, x: int, y: int, width: int) -> np.ndarray:
        """ A slice of the image across all bands """
        pixels = self.dataset.ReadAsArray(x, y, width, width)
        if self.band_count > 1:
            pixels = pixels.transpose(1, 2, 0)
        return pixels
