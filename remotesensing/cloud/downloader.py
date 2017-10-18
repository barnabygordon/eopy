import os
from urllib import request

from osgeo import gdal
from tqdm import tqdm

from remotesensing.cloud.calibration import Calibration
from remotesensing.image import Image
from remotesensing.image.sensor import Landsat8
from remotesensing.image.sensor import Sentinel2


class Downloader:
    """ A class for downloading satellite imagery """
    def __init__(self, save_directory):
        """
        :type save_directory: str
        """
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

    def get_landsat8_bands(self, scene, band_list, calibrate=True):
        """ Load Landsat-8 bands into memory

        An example of a landsat url is:
        https://landsat-pds.s3.amazonaws.com/c1/L8/139/045/LC08_L1TP_139045_20170304_20170316_01_T1/LC08_L1TP_139045_20170304_20170316_01_T1_B1.TIF

        :type scene: cloud.scene.LandsatScene
        :type band_list: list[str]
        :type calibrate: bool
        :rtype: image.Image
        """

        images = []
        for band in band_list:
            url = scene.get_download_path_for_band(band)
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

    def get_sentinel2_bands(self, scene, band_list, calibrate=False):
        """ Load a Sentinel-2 band into memory

        An example of a Sentinel-2 url is:
        http://sentinel-s2-l1c.s3.amazonaws.com/tiles/10/S/DG/2015/12/7/0/B01.jp2

        :type scene: cloud.scene.SentinelScene
        :type band_list: list[str]
        :type calibrate: bool
        :rtype: image.Image
        """
        if calibrate:
            raise NotImplementedError("Coming soon!")

        images = []
        for band in tqdm(band_list, total=len(band_list), desc="Downloading image"):
            band_name = "B{}".format(self.sentinel_2.band_number(band))
            filename = "S2A_{date}_{band}.jp2".format(date=scene.date, band=band_name)

            save_path = os.path.join(self.save_directory, filename)
            url = "{}/{}.jp2".format(scene.image_url, band_name)

            request.urlretrieve(url, save_path)
            images.append(Image.load(save_path))

        if len(band_list) > 1:
            return Image.stack(images)
        else:
            return images[0]
