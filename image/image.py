import numpy as np
import os
from osgeo import gdal, osr
from tqdm import tqdm
from shapely.geometry import Polygon
from typing import List

from image.geotransform import Geotransform
from tools import gis

GTIFF_DRIVER = 'GTiff'


class Image:
    """ A generic image object revolving around gdal """
    def __init__(self, pixels, geotransform, projection, metadata=None, band_labels: dict=None):
        self.pixels = pixels
        self.geotransform = geotransform
        self.projection = projection
        self.metadata = metadata
        self.band_labels = band_labels

    def __repr__(self):
        return "Image - Shape: {}x{}x{} | EPSG: {}".format(self.width, self.height, self.band_count, self.epsg)

    @classmethod
    def load(cls, filepath: str, band_labels: {str: int}=None):
        if not os.path.exists(filepath):
            raise UserWarning("Filepath does not exist.")
        image_dataset = gdal.Open(filepath)
        pixels = image_dataset.ReadAsArray()
        if pixels.ndim > 2:
            pixels = pixels.transpose(1, 2, 0)

        geotransform = Geotransform(image_dataset.GetGeoTransform())
        projection = image_dataset.GetProjection()
        metadata = image_dataset.GetMetadata()

        return Image(pixels, geotransform, projection, metadata=metadata, band_labels=band_labels)

    @property
    def width(self) -> int:
        return self.pixels.shape[0]

    @property
    def height(self) -> int:
        return self.pixels.shape[1]

    @property
    def band_count(self) -> int:
        if self.pixels.ndim > 2:
            return self.pixels.shape[2]
        else:
            return 1

    @property
    def shape(self) -> (int, int, int):
        return self.pixels.shape

    @property
    def bounds(self) -> Polygon:
        x_max = self.geotransform.upper_left_x + (self.width * self.geotransform.pixel_width)
        y_min = self.geotransform.upper_left_y - (self.height * self.geotransform.pixel_width)
        x = [self.geotransform.upper_left_x, x_max, x_max,
             self.geotransform.upper_left_x, self.geotransform.upper_left_x]
        y = [self.geotransform.upper_left_y, self.geotransform.upper_left_y,
             y_min, y_min, self.geotransform.upper_left_y]

        return Polygon(zip(x, y))

    @property
    def epsg(self) -> int:
        spatial_reference = osr.SpatialReference(wkt=self.projection)
        return spatial_reference.GetAttrValue("AUTHORITY", 1)

    def get_subset(self, x: int, y: int, width: int) -> np.ndarray:
        """ A slice of the image across all bands """
        pixels = self.pixels[y:y+width, x:x+width]
        geotransform = self._subset_geotransform(x, y)
        return Image(pixels, geotransform, self.projection, self.metadata, band_labels=self.band_labels)

    def _subset_geotransform(self, x, y):
        upper_left_x, upper_left_y = gis.pixel_to_world(x, y, self.geotransform)
        return Geotransform((upper_left_x, self.geotransform.pixel_width, self.geotransform.rotation_x,
                             upper_left_y, self.geotransform.rotation_y, self.geotransform.pixel_height))

    def stack(self, images: List["Image"]) -> (np.ndarray, gdal.Dataset):
        """ Stack a list of Image objects and return a single image array and dataset """
        if len(images) == 1:
            return Image(images[0].pixels, self.geotransform, self.projection)
        else:
            stack = np.zeros((images[0].height, images[0].width, len(images)))

            for i, image in tqdm(enumerate(images), total=len(images), desc='Stacking bands'):
                stack[:, :, i] = image.pixels

            return Image(stack, self.geotransform, self.projection, self.metadata, band_labels=self.band_labels)

    def save(self, filepath: str, data_type: int = gdal.GDT_Int16) -> None:
        """ Save a ndarray as an image with geospatial metadata
        :param image: ndarray with shape (x, y) or (x, y, z)
        :param image_dataset: a gdal Dataset returned from gdal.Open
        :param filepath: path to which the image should be saved, including extension
        :param data_type: Type of bit depth for the output image
        """

        out_image = gdal.GetDriverByName(GTIFF_DRIVER)\
            .Create(filepath, self.height, self.width, self.band_count, data_type)
        out_image.SetGeoTransform(self.geotransform.geotransform)
        out_image.SetProjection(self.projection)

        if self.band_count > 1:
            for band in range(self.band_count):
                out_image.GetRasterBand(band+1).WriteArray(self.pixels[:, :, band])
        else:
            out_image.GetRasterBand(1).WriteArray(self.pixels)

        out_image.FlushCache()
