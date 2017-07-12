from osgeo import gdal
from tqdm import tqdm
import numpy as np

from image.scene import LandsatScene
from image.scene import SentinelScene
from image.sensor import Landsat8
from image.sensor import Sentinel2
from image import Image

GTIFF_DRIVER = 'GTiff'


class Downloader:
    """ A class for downloading satellite imagery """
    def __init__(self, filepath: str, data_type: int = gdal.GDT_Float32):
        self.filepath = filepath
        self.data_type = data_type

    @property
    def available_landsat8_bands(self):
        """ List the available Landsat-8 band options"""
        return Landsat8.available_bands

    @property
    def available_sentinel2_bands(self):
        """ List the available Sentinel-2 band options """
        return Sentinel2.available_bands

    def get_landsat8_bands(self, scene: LandsatScene, band_list: [str]) -> Image:
        """ Load a Landsat-8 band into memory
        :param scene: A LandsatScene from the Searcher
        :param band_list: List of the bands you want to download
        :return: An Image object
        """

        url = scene.download_links[Landsat8.band_number(band_list[0])]
        image_dataset = gdal.Open('/vsicurl/{}'.format(url))
        image = Image(image_dataset)

        if len(band_list) > 1:
            image_stack = np.zeros((image.height, image.width, len(band_list)))
            image_stack[:, :, 0] = image.pixels

            for i, band in tqdm(enumerate(band_list[1:]), total=len(band_list[1:])):
                url = scene.download_links[Landsat8.band_number(band)]
                image_dataset = gdal.Open('/vsicurl/{}'.format(url))
                image = Image(image_dataset)

                image_stack[:, :, i+1] = image.pixels

        else:
            image_stack = image.pixels

        self.save_image(image_stack, image_dataset)

        return Image(gdal.Open(self.filepath))

    def get_sentinel2_band(self, scene: SentinelScene, band: str) -> Image:
        raise NotImplementedError("Sorry! Work in progress!")

    def save_image(self, image: np.ndarray, image_dataset: gdal.Dataset) -> None:
        """ Save a ndarray as an image with geospatial metadata
        :param image: ndarray with shape (x, y) or (x, y, z)
        :param image_dataset: a gdal Dataset returned from gdal.Open
        """
        width = image.shape[0]
        height = image.shape[1]

        if image.ndim > 2:
            number_of_bands = image.shape[2]
        else:
            number_of_bands = 1

        out_image = gdal.GetDriverByName(GTIFF_DRIVER)\
            .Create(self.filepath, height, width, number_of_bands, self.data_type)
        out_image.SetGeoTransform(image_dataset.GetGeoTransform())
        out_image.SetProjection(image_dataset.GetProjection())

        if number_of_bands > 1:
            for band in range(number_of_bands):
                out_image.GetRasterBand(band+1).WriteArray(image[:, :, band])
        else:
            out_image.GetRasterBand(1).WriteArray(image)

        out_image.FlushCache()
