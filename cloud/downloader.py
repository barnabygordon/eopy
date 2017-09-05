import os
from urllib import request
from tqdm import tqdm
from osgeo import gdal

from cloud.calibration import Calibration
from cloud.scene import LandsatScene
from cloud.scene import SentinelScene
from image import Image
from image.sensor import Landsat8
from image.sensor import Sentinel2


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
            images.append(Image.load_from_dataset(image_dataset))

        image_stack = Image.stack(images, band_labels={i+1: value for i, value in enumerate(band_list)})

        if calibrate:
            metadata_url = "{download_path}_MTL.txt".format(download_path=scene.download_path)
            calibrator = Calibration(metadata_url=metadata_url)
            image_stack = calibrator.calibrate_landsat(image_stack, band_list)

        filename = "LS8_{date}_{path}_{row}.tif".format(date=scene.date, path=scene.path, row=scene.row)
        save_path = os.path.join(self.save_directory, filename)
        image_stack.save(save_path, data_type='float32')

        return image_stack

    def get_sentinel2_band(self, scene: SentinelScene, band_list: [str], calibrate: bool=False) -> Image:
        """ Load a Sentinel-2 band into memory

        An example of a Sentinel-2 url is:
        http://sentinel-s2-l1c.s3.amazonaws.com/tiles/10/S/DG/2015/12/7/0/B01.jp2

        :param scene: A Sentinel-2 scene
        :param band_list: A list of bands to download
        :param calibrate: Pre calibrate the images
        :return: An Image object
        """
        if calibrate:
            raise NotImplementedError("Coming soon!")

        images = []
        for band in tqdm(band_list, total=len(band_list), desc="Downloading image"):
            band_name = "B{}".format(self.sentinel_2.band_number(band))
            filename = "S2A_{date}_{band}.jp2".format(date=scene.date, band=band_name)

            save_path = os.path.join(self.save_directory, filename)
            request.urlretrieve("{}/{}.jp2".format(scene.image_url, band_name), save_path)
            images.append(Image.load(save_path))

        if len(band_list) > 1:
            return Image.stack(images, band_labels={i+1: value for i, value in enumerate(band_list)})
        else:
            return images[0]
