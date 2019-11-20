from typing import List
from shapely.geometry import Polygon

from remotesensing.image import Loader
from remotesensing.image import Image
from remotesensing.image.sensor import Landsat8
from remotesensing.image.sensor import Sentinel2
from remotesensing.cloud.scene import Scene


class Downloader:
    """ A class for downloading satellite imagery """
    def __init__(self):

        self._landsat_8 = Landsat8()
        self._sentinel_2 = Sentinel2()
        self._image_loader = Loader()

    @property
    def available_landsat8_bands(self) -> str:
        """ List the available Landsat-8 band options"""

        return ", ".join(self._landsat_8.bands)

    @property
    def available_sentinel2_bands(self) -> str:
        """ List the available Sentinel-2 band options """

        return ", ".join(self._sentinel_2.bands)

    def download(self, scene: Scene, bands: List[str], extent: Polygon = None) -> Image:

        if len(bands) > 1:
            return Image.stack([self._image_loader.load(self._get_url(scene, band), extent=extent) for band in bands])
        else:
            return self._image_loader.load(self._get_url(scene, bands[0]), extent=extent)

    @staticmethod
    def _get_url(scene: Scene, band: str) -> str:

        try:
            return scene.links[band]['href']
        except KeyError:
            raise UserWarning(f'Band {band} is invalid')
