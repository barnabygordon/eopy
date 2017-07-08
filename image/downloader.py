from osgeo import gdal

from image.scene import LandsatScene, SentinelScene
from image import Image

LANDSAT_8_LOOKUP_BAND = {
    'coastal': 1, 'blue': 2, 'green': 3, 'red': 4,
    'nir': 5, 'swir_1': 6, 'swir_2': 7, 'pan': 8,
    'cirrus': 9, 'tirs_1': 10, 'tirs_2': 11, 'BQA': 12}


class Downloader:
    @staticmethod
    def available_landsat8_bands():
        """ List the available Landsat-8 band options"""
        return list(LANDSAT_8_LOOKUP_BAND.keys())

    @staticmethod
    def get_landsat8_band(scene: LandsatScene, band: str) -> Image:
        """ Load a Landsat-8 band into memory
        :param scene: A LandsatScene from the Searcher
        :param band: Name of the band you want to download
        :return: An Image object
        """
        url = scene.download_links[LANDSAT_8_LOOKUP_BAND[band]]
        image_dataset = gdal.Open('/vsicurl/{}'.format(url))

        return Image(image_dataset)

    @staticmethod
    def get_sentinel2_band(scene: SentinelScene, band: str) -> Image:
        raise NotImplementedError("Sorry! Work in progress!")
