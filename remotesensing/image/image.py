import os

import numpy as np
from osgeo import gdal, osr
from tqdm import tqdm

from remotesensing.image import Geotransform
from remotesensing.tools import gis

GTIFF_DRIVER = 'GTiff'


class Image:
    """ A generic image object using gdal """
    def __init__(self, pixels, geotransform, projection, metadata=None, band_labels=None):
        """
        :type pixels: numpy.ndarray
        :type geotransform: geotransform.Geotransform
        :param projection: str
        :param metadata: dict
        :param band_labels: dict
        """
        self.pixels = pixels
        self.data_type = self.pixels.dtype
        self.geotransform = geotransform
        self.projection = projection
        self.metadata = metadata
        self.band_labels = band_labels

    def __repr__(self) -> str:
        return "Image - Shape: {}x{}x{} | EPSG: {}".format(self.width, self.height, self.band_count, self.epsg)

    def __getitem__(self, band):
        """
        :type band: list[int, str
        :rtype: image.Image
        """
        if type(band) == int:
            image = self.pixels[:, :, band]
            if bool(self.band_labels):
                band_labels = {list(self.band_labels)[band]: 1}
            else:
                band_labels = None
        elif type(band) == str:
            image = self._get_band_by_number(self.band_labels[band])
            band_labels = {band: 1}
        else:
            raise UserWarning("Requires a integer or a string")

        return Image(image, self.geotransform, self.projection,
                     band_labels=band_labels, metadata=self.metadata)

    def _get_band_by_number(self, band_number):
        """
        :type band_number: int
        :rtype: numpy.ndarray
        """
        return self.pixels[:, :, band_number-1]

    @classmethod
    def load(cls, filepath, band_labels=None):
        """
        :type filepath: str
        :type band_labels: dict{str: int}
        :rtype: image.Image
        """
        if not os.path.exists(filepath):
            raise UserWarning("Filepath does not exist.")

        return cls.load_from_dataset(gdal.Open(filepath), band_labels)

    @classmethod
    def load_from_dataset(cls, image_dataset, band_labels=None):
        """
        :type image_dataset: osgeo.gdal.Dataset
        :type band_labels: dict
        :rtype: image.Image
        """
        geotransform = Geotransform(image_dataset.GetGeoTransform())
        projection = image_dataset.GetProjection()
        metadata = image_dataset.GetMetadata()
        pixels = image_dataset.ReadAsArray()

        if pixels.ndim > 2:
            pixels = pixels.transpose(1, 2, 0)

        return Image(pixels, geotransform, projection, metadata=metadata, band_labels=band_labels)

    @property
    def width(self):
        """
        :rtype: int
        """
        return self.pixels.shape[0]

    @property
    def height(self):
        """
        :rtype: int
        """
        return self.pixels.shape[1]

    @property
    def band_count(self):
        """
        :rtype: int
        """
        if self.pixels.ndim > 2:
            return self.pixels.shape[2]
        else:
            return 1

    @property
    def shape(self):
        """
        :rtype: tuple(int)
        """
        return self.pixels.shape

    @property
    def dtype(self):
        """
        :rtype: str
        """
        return self.pixels.dtype

    @property
    def epsg(self):
        """
        :rtype: int
        """
        spatial_reference = osr.SpatialReference(wkt=self.projection)
        return spatial_reference.GetAttrValue("AUTHORITY", 1)

    def subset(self, x, y, width, height=None):
        """ A slice of the image across all bands
        :type x: int
        :type y: int
        :type width: int
        :type height: int
        :rtype: image.Image
        """
        if height is None:
            height = width
        pixels = self.pixels[y:y+height, x:x+width]
        geotransform = self._subset_geotransform(x, y)
        return Image(pixels, geotransform, self.projection, self.metadata, band_labels=self.band_labels)

    def _subset_geotransform(self, x, y):
        """ Update the image geotransform based on the new subset coordinates
        :param x: int
        :param y: int
        :return: geotransform.Geotransform
        """
        upper_left_x, upper_left_y = gis.pixel_to_world(x, y, self.geotransform)
        return Geotransform((upper_left_x, self.geotransform.pixel_width, self.geotransform.rotation_x,
                             upper_left_y, self.geotransform.rotation_y, self.geotransform.pixel_height))

    def clip_with(self, polygon, mask_value=np.nan):
        """
        :param polygon: shapely.Polygon
        :param mask_value: float
        :rtype: image.Image
        """
        return gis.clip_image(self, polygon, mask_value=mask_value)

    @staticmethod
    def stack(images):
        """ Stack a list of Image objects and return a single Image
        :param images: list[image.Image]
        :return: image.Image
        """
        if len(images) == 1:
            raise UserWarning("Only one image has been provided")
        else:
            stack = np.zeros((images[0].width, images[0].height, len(images)))

            for i, image in tqdm(enumerate(images), total=len(images), desc='Stacking bands'):
                stack[:, :, i] = image.pixels

            band_labels = {list(image.band_labels)[0]: i+1 for i, image in enumerate(images)
                           if image.band_labels is not None}
            return Image(stack,
                         images[0].geotransform, images[0].projection, images[0].metadata,
                         band_labels=band_labels)

    def save(self, filepath, data_type='uint16'):
        """ Save a ndarray as an image with geospatial metadata
        :type filepath: str
        :type data_type: str
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
