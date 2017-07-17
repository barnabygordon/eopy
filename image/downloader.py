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

GTIFF_DRIVER = 'GTiff'


class Downloader:
    """ A class for downloading satellite imagery """
    def __init__(self, save_directory: str, data_type: int = gdal.GDT_Int16):
        self.save_directory = save_directory
        self.data_type = data_type
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
        """ Load a Landsat-8 band into memory
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
        self.save_image(image_stack, image_dataset, filepath=save_path)

        return Image(gdal.Open(save_path))

    def get_sentinel2_band(self, scene: SentinelScene, band: str) -> Image:
        filename = "S2A_{date}_{band}".format(date=scene.date, band=band)
        save_path = os.path.join(self.save_directory, filename)
        request.urlretrieve(scene.image_url, save_path)

        return Image(gdal.Open(save_path))

    def save_image(self, image: np.ndarray, image_dataset: gdal.Dataset, filepath: str) -> None:
        """ Save a ndarray as an image with geospatial metadata
        :param image: ndarray with shape (x, y) or (x, y, z)
        :param image_dataset: a gdal Dataset returned from gdal.Open
        :param filepath: path to which the image should be saved, including extension
        """
        width = image.shape[0]
        height = image.shape[1]

        if image.ndim > 2:
            number_of_bands = image.shape[2]
        else:
            number_of_bands = 1

        out_image = gdal.GetDriverByName(GTIFF_DRIVER)\
            .Create(filepath, height, width, number_of_bands, self.data_type)
        out_image.SetGeoTransform(image_dataset.GetGeoTransform())
        out_image.SetProjection(image_dataset.GetProjection())

        if number_of_bands > 1:
            for band in range(number_of_bands):
                out_image.GetRasterBand(band+1).WriteArray(image[:, :, band])
        else:
            out_image.GetRasterBand(1).WriteArray(image)

        out_image.FlushCache()
