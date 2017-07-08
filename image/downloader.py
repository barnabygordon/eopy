from osgeo import gdal

from image import LandsatScene
from image import Image

LANDSAT_8_LOOKUP_BAND = {
    'coastal': 1, 'blue': 2, 'green': 3, 'red': 4,
    'nir': 5, 'swir_1': 6, 'swir_2': 7, 'pan': 8,
    'cirrus': 9, 'tirs_1': 10, 'tirs_2': 11, 'BQA': 12}


class Downloader:
    @staticmethod
    def get_landsat8_band(scene: LandsatScene, band) -> Image:
        url = scene.download_links[LANDSAT_8_LOOKUP_BAND[band]]
        image_dataset = gdal.Open('/vsicurl/{}'.format(url))

        return Image(image_dataset)
