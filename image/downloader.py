from osgeo import gdal
from urllib import request
import os

from image.scene import LandsatScene
from image.scene import SentinelScene
from image.sensor import Landsat8
from image.sensor import Sentinel2
from image.calibration import Calibration
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

    def get_landsat8_bands(self, scene: LandsatScene, band_list: [str], calibrate: bool=True) -> Image:
        """ Load Landsat-8 bands into memory

        An example of a landsat url is:
        https://landsat-pds.s3.amazonaws.com/c1/L8/139/045/LC08_L1TP_139045_20170304_20170316_01_T1/LC08_L1TP_139045_20170304_20170316_01_T1_B1.TIF

        :param scene: A LandsatScene from the Searcher
        :param band_list: List of the bands you want to download
        :param calibrate: Do you want to calibrate the image to Top of Atmosphere reflectance?
        :return: An Image object
        """

        images = []
        for band in band_list:
            url = "{download_path}_B{band}.TIF".format(download_path=scene.download_path,
                                                       band=self.landsat_8.band_number(band))
            image_dataset = gdal.Open('/vsicurl/{}'.format(url))
            images.append(Image(image_dataset))

        image_stack, image_dataset = Image.stack(images)

        if calibrate:
            metadata_url = "{download_path}_MTL.txt".format(download_path=scene.download_path)
            calibrator = Calibration(metadata_url=metadata_url)
            image_stack = calibrator.calibrate_landsat(image_stack, band_list)

        filename = "LS8_{date}_{bands}.tif".format(date=scene.date, bands='b'.join(band_list))
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
        band_name = "B{}".format(self.sentinel_2.band_number(band))
        filename = "S2A_{date}_{band}.jp2".format(date=scene.date, band=band_name)

        save_path = os.path.join(self.save_directory, filename)
        request.urlretrieve("{}/{}.jp2".format(scene.image_url, band_name), save_path)

        return Image(gdal.Open(save_path))
