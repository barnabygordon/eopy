from osgeo import gdal
from tqdm import tqdm
from urllib import request
import numpy as np
import os

from image.scene import LandsatScene
from image.scene import SentinelScene
from image.sensor import Landsat8
from image.sensor import Sentinel2
from image import Image


class Downloader:
    """ A class for downloading satellite imagery """
    def __init__(self, save_directory: str):
        self.save_directory = save_directory
        self.landsat_8 = Landsat8()
        self.sentinel_2 = Sentinel2()

    @property
    def available_landsat8_bands(self):
        """ List the available Landsat-8 band options"""
        return ", ".join(self.landsat_8.available_bands)

    @property
    def available_sentinel2_bands(self):
        """ List the available Sentinel-2 band options """
        return ", ".join(self.sentinel_2.available_bands)

    def get_landsat8_bands(self, scene: LandsatScene, band_list: [str]) -> Image:
        """ Load Landsat-8 bands into memory

        An example of a landsat url is:
        https://landsat-pds.s3.amazonaws.com/c1/L8/139/045/LC08_L1TP_139045_20170304_20170316_01_T1/LC08_L1TP_139045_20170304_20170316_01_T1_B1.TIF

        :param scene: A LandsatScene from the Searcher
        :param band_list: List of the bands you want to download
        :return: An Image object
        """
        progress_bar = tqdm(total=len(band_list))

        url = scene.download_links[self.sentinel_2.band_number(band_list[0])]
        image_dataset = gdal.Open('/vsicurl/{}'.format(url))
        image = Image(image_dataset)
        progress_bar.update(1)

        if len(band_list) > 1:
            image_stack = np.zeros((image.height, image.width, len(band_list)))
            image_stack[:, :, 0] = image.pixels

            for i, band in enumerate(band_list[1:]):
                url = scene.download_links[self.landsat_8.band_number(band)]
                image_dataset = gdal.Open('/vsicurl/{}'.format(url))
                image = Image(image_dataset)

                image_stack[:, :, i+1] = image.pixels
                progress_bar.update(1)

        else:
            image_stack = image.pixels

        filename = "LS8_{date}.tif".format(date=scene.date)
        save_path = os.path.join(self.save_directory, filename)
        Image.save(image_stack, image_dataset, filepath=save_path)

        return Image(gdal.Open(save_path))

    def get_sentinel2_band(self, scene: SentinelScene, band: str) -> Image:
        """ Load a Sentinel-2 band into memory

        An example of a Sentinel-2 url is:
        http://sentinel-s2-l1c.s3.amazonaws.com/tiles/10/S/DG/2015/12/7/0/B01.jp2

        :param scene: A Sentinel-2 scene
        :param band: A band string
        :return: An Image object
        """
        filename = "S2A_{date}_{band}".format(date=scene.date, band=band)
        save_path = os.path.join(self.save_directory, filename)
        request.urlretrieve(scene.image_url, save_path)

        return Image(gdal.Open(save_path))
