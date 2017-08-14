import numpy as np
from osgeo import gdal, osr
from tqdm import tqdm
from shapely.geometry import Polygon
from typing import List

from image.geotransform import Geotransform

GTIFF_DRIVER = 'GTiff'


class Image:
    """ A generic image object revolving around gdal """
    def __init__(self, image_dataset: gdal.Dataset):
        self.dataset = image_dataset
        self.geotransform = Geotransform(self.dataset.GetGeoTransform())

    def __repr__(self):
        return "Image - Shape: {}x{}x{} | EPSG: {}".format(self.width, self.height, self.band_count, self.epsg)

    @classmethod
    def load(cls, filepath: str):
        image_dataset = gdal.Open(filepath)
        assert image_dataset is not None, "File is not a valid image"
        return Image(image_dataset)

    @property
    def width(self) -> int:
        return self.dataset.RasterXSize

    @property
    def height(self) -> int:
        return self.dataset.RasterYSize

    @property
    def shape(self) -> (int, int, int):
        return self.width, self.height, self.band_count

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
    def band_count(self) -> int:
        return self.dataset.RasterCount

    @property
    def pixels(self) -> np.ndarray:
        """ The pixels data as a ndarray """
        pixels = self.dataset.ReadAsArray()
        if self.band_count > 1:
            return pixels.transpose(1, 2, 0)
        else:
            return pixels

    @property
    def projection(self) -> str:
        """ The projection of the image as a WKT string """
        return self.dataset.GetProjection()

    @property
    def metadata(self) -> {str: str}:
        """ The metadata of the image as a dictionary """
        return self.dataset.GetMetadata()

    @property
    def epsg(self) -> int:
        spatial_reference = osr.SpatialReference(wkt=self.projection)
        return spatial_reference.GetAttrValue("AUTHORITY", 1)

    def get_window(self, x: int, y: int, width: int) -> np.ndarray:
        """ A slice of the image across all bands """
        pixels = self.dataset.ReadAsArray(x, y, width, width)
        if self.band_count > 1:
            pixels = pixels.transpose(1, 2, 0)
        return pixels

    @staticmethod
    def stack(images: List["Image"]) -> (np.ndarray, gdal.Dataset):
        """ Stack a list of Image objects and return a single image array and dataset """
        if len(images) == 1:
            return images[0].pixels, images[0].dataset
        else:
            stack = np.zeros((images[0].height, images[0].width, len(images)))

            for i, image in tqdm(enumerate(images), total=len(images), desc='Stacking bands'):
                stack[:, :, i] = image.pixels

            return stack, images[0].dataset

    @staticmethod
    def save(image: np.ndarray,
             projection: str,
             geotransform: Geotransform,
             filepath: str,
             data_type: int = gdal.GDT_Int16) -> None:
        """ Save a ndarray as an image with geospatial metadata
        :param image: ndarray with shape (x, y) or (x, y, z)
        :param image_dataset: a gdal Dataset returned from gdal.Open
        :param filepath: path to which the image should be saved, including extension
        :param data_type: Type of bit depth for the output image
        """
        width = image.shape[0]
        height = image.shape[1]

        if image.ndim > 2:
            number_of_bands = image.shape[2]
        else:
            number_of_bands = 1

        out_image = gdal.GetDriverByName(GTIFF_DRIVER)\
            .Create(filepath, height, width, number_of_bands, data_type)
        out_image.SetGeoTransform(geotransform.geotransform)
        out_image.SetProjection(projection)

        if number_of_bands > 1:
            for band in range(number_of_bands):
                out_image.GetRasterBand(band+1).WriteArray(image[:, :, band])
        else:
            out_image.GetRasterBand(1).WriteArray(image)

        out_image.FlushCache()
