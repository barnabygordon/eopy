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
            return Image.stack([self._image_loader.load(self._get_url_for_band_name(scene, band), extent=extent) for band in bands])

        else:
            return self._image_loader.load(self._get_url_for_band_name(scene, bands[0]), extent=extent)

    def _get_url_for_band_name(self, scene: Scene, band_name: str) -> str:

        if scene.satellite_name == 'landsat-8':
            band_url = scene.links[self._landsat_8.bands[band_name]]
            return self._compute_gdal_virtual_url(band_url)

        elif scene.satellite_name == 'Sentinel-2A':
            band_url = scene.links[self._sentinel_2.bands[band_name]]
            return self._compute_gdal_virtual_url(band_url)

    def _compute_gdal_virtual_url(self, url: str) -> str:

        return f"/vsicurl/{url.split('https://')[1]}"
