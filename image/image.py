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
    """ A generic image object using gdal """
    def __init__(self,
                 pixels: np.ndarray,
                 geotransform: Geotransform,
                 projection: str, metadata=None,
                 band_labels: dict=None):
        self.pixels = pixels
        self.data_type = self.pixels.dtype
        self.geotransform = geotransform
        self.projection = projection
        self.metadata = metadata
        self.band_labels = band_labels

    def __repr__(self) -> str:
        return "Image - Shape: {}x{}x{} | EPSG: {}".format(self.width, self.height, self.band_count, self.epsg)

    def __getitem__(self, band: int) -> "Image":
        return Image(self.pixels[:, :, band], self.geotransform, self.projection, self.metadata)

    @classmethod
    def load(cls, filepath: str, band_labels: {str: int}=None) -> "Image":
        if not os.path.exists(filepath):
            raise UserWarning("Filepath does not exist.")

        return cls.load_from_dataset(gdal.Open(filepath), band_labels)

    @classmethod
    def load_from_dataset(cls, image_dataset: gdal.Dataset, band_labels: dict=None) -> "Image":
        geotransform = Geotransform(image_dataset.GetGeoTransform())
        projection = image_dataset.GetProjection()
        metadata = image_dataset.GetMetadata()
        pixels = image_dataset.ReadAsArray()

        if pixels.ndim > 2:
            pixels = pixels.transpose(1, 2, 0)

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
    def dtype(self) -> str:
        return self.pixels.dtype

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

    def get_composite(self, bands: [str]):
        if self.band_labels is None:
            raise UserWarning("Band labels must be defined.")
        else:
            composite = np.zeros((self.width, self.height, len(bands)))
            for i, b in enumerate(bands):
                band_number = self.band_labels[b]
                composite[:, :, i] = self.pixels[:, :, band_number-1]

            return Image(composite, self.geotransform, self.projection, self.metadata,
                         band_labels={i+1: value for i, value in enumerate(bands)})

    def subset(self, x: int, y: int, width: int, height: int=None) -> np.ndarray:
        """ A slice of the image across all bands """
        if height is None:
            height = width
        pixels = self.pixels[y:y+height, x:x+width]
        geotransform = self._subset_geotransform(x, y)
        return Image(pixels, geotransform, self.projection, self.metadata, band_labels=self.band_labels)

    def clip_with(self, polygon: Polygon, mask_value: float=np.nan):
        return gis.clip_image(self, polygon, mask_value=mask_value)

    def _subset_geotransform(self, x, y) -> Geotransform:
        """ Update the image geotransform based on new subset coordinates """
        upper_left_x, upper_left_y = gis.pixel_to_world(x, y, self.geotransform)
        return Geotransform((upper_left_x, self.geotransform.pixel_width, self.geotransform.rotation_x,
                             upper_left_y, self.geotransform.rotation_y, self.geotransform.pixel_height))

    @staticmethod
    def stack(images: List["Image"], band_labels: {str: int}=None) -> (np.ndarray, gdal.Dataset):
        """ Stack a list of Image objects and return a single image array and dataset """
        if len(images) == 1:
            raise UserWarning("Only one image has been provided")
        else:
            stack = np.zeros((images[0].width, images[0].height, len(images)))

            for i, image in tqdm(enumerate(images), total=len(images), desc='Stacking bands'):
                stack[:, :, i] = image.pixels

            return Image(stack,
                         images[0].geotransform, images[0].projection, images[0].metadata,
                         band_labels=band_labels)

    def save(self, filepath: str, data_type: str='uint16') -> None:
        """ Save a ndarray as an image with geospatial metadata
        :param filepath: path to which the image should be saved, including extension
        :param data_type: Type of bit depth for the output image
        """

        gdal_data_type = self._get_gdal_data_type(data_type)
        out_image = gdal.GetDriverByName(GTIFF_DRIVER)\
            .Create(filepath, self.height, self.width, self.band_count, gdal_data_type)
        out_image.SetGeoTransform(self.geotransform.tuple)
        out_image.SetProjection(self.projection)

        if self.band_count > 1:
            for band in range(self.band_count):
                out_image.GetRasterBand(band+1).WriteArray(self.pixels[:, :, band])
        else:
            out_image.GetRasterBand(1).WriteArray(self.pixels)

        out_image.FlushCache()

    @staticmethod
    def _get_gdal_data_type(name):
        if name == 'uint8':
            return gdal.GDT_Byte
        elif name == 'uint16':
            return gdal.GDT_UInt16
        elif name == 'float32':
            return gdal.GDT_Float32
        else:
            raise UserWarning("Unrecognised data type.")
