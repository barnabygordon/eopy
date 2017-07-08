import numpy as np
from osgeo import gdal
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
        pixels = self.dataset.ReadAsArray()
        if pixels.ndim > 2:
            return pixels.transpose(1, 2, 0)
        else:
            return pixels

    def get_window(self, x: int, y: int, width: int) -> np.ndarray:
        return self.dataset.ReadAsArray(x, y, width, width)
