import gdal
import requests
from pyproj import CRS
from pyproj.exceptions import CRSError
from urllib.request import urlretrieve
from http import HTTPStatus
from typing import List

from remotesensing.geometry import GeoPolygon
from remotesensing.cloud.scene import Scene
from remotesensing.image import Image, Loader


class Downloader:

    def __init__(self, download_directory: str = ''):

        self._image_loader = Loader()
        self._download_directory = download_directory

    def download(self, scene: Scene, bands: List[str]):

        for band in bands:

            try:
                url = self._get_url(scene, band)
            except UserWarning as e:
                print(e)
                continue

            response = requests.head(url)
            if response.status_code != HTTPStatus.OK:
                print(f'Unable to download {band}: {response.status_code} {response.reason}')
                continue

            self._download_from_url(url, file_name=scene.identity)

    def stream(self, scene: Scene, bands: List[str], boundary: GeoPolygon = None) -> Image:

        band_stack = []
        for band in bands:
            try:
                url = self._get_url(scene, band)
            except UserWarning as e:
                print(e)
                continue

            image_dataset = gdal.Open('/vsicurl/' + url)
            if not image_dataset:
                raise UserWarning(f'Unable to stream band: {band} {url}')
            if boundary:
                try:
                    crs = CRS(image_dataset.GetProjection())
                    boundary = boundary.transform(crs.to_epsg())
                except CRSError:
                    continue
                band = self._image_loader.load_from_dataset_and_clip(image_dataset, boundary)
            else:
                band = self._image_loader.load_from_dataset(image_dataset)
            band_stack.append(band)

        if len(band_stack) > 1:
            return Image.stack(band_stack)
        else:
            return band_stack[0]

    @staticmethod
    def _get_url(scene: Scene, band: str) -> str:

        try:
            return scene.links[band]['href']
        except KeyError:
            raise UserWarning(f'Band {band} does not exist {scene.links}')

    def _download_from_url(self, url: str, file_name: str):

        urlretrieve(url, f'{self._download_directory}/{file_name}.tif')
