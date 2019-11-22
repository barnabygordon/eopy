import requests
from http import HTTPStatus
from typing import List

from remotesensing.cloud.scene import Scene


class Downloader:

    def __init__(self, download_directory: str):

        self._download_directory = download_directory

    def download(self, scene: Scene, bands: List[str]):

        for band in bands:
            try:
                url = scene.links[band]['href']
            except KeyError:
                print(f'Band {band} does not exist')
                continue

            response = requests.head(url)
            if response.status_code != HTTPStatus.OK:
                print(f'Unable to download {band}: {response.status_code} {response.reason}')
                continue

            self._download_from_url(url)

    def _download_from_url(self, url: str):
        pass
