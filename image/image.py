import numpy as np
from image import Geotransform

BAND_LOOKUP = {'blue': 1, 'green': 2, 'red': 3, 'red_edge': 4, 'nir': 5}


class Image:
    def __init__(self, image_dataset):
        self.image_dataset = image_dataset
        self.geotransform = Geotransform(self.image_dataset)

    @property
    def width(self) -> int:
        return self.image_dataset.RasterXSize

    @property
    def height(self) -> int:
        return self.image_dataset.RasterYSize

    @property
    def band_count(self) -> int:
        return self.image_dataset.RasterCount

    @property
    def ndvi(self) -> np.ndarray:
        nir = self.get_band('nir')
        red = self.get_band('red')
        return (nir - red) / (nir + red)

    def get_band(self, band: str) -> np.ndarray:
        band_dataset = self.image_dataset.GetRasterBand(BAND_LOOKUP[band])
        return band_dataset.ReadAsArray()

    def get_window(self, x: int, y: int, width: int) -> np.ndarray:
        return self.image_dataset.ReadAsArray(x, y, width, width)

