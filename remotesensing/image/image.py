import numpy as np
from scipy import ndimage
from typing import List, Tuple
from osgeo import gdal, osr
from tqdm import tqdm
from shapely.geometry import Polygon

from remotesensing.tools import gis
from remotesensing.image import Geotransform

GTIFF_DRIVER = 'GTiff'


class Image:
    """ A generic image object using gdal """
    def __init__(self, pixels: np.ndarray, geotransform: Geotransform, projection: str, band_labels: dict = None):

        self.pixels = pixels
        self.data_type = self.pixels.dtype
        self.geotransform = geotransform
        self.projection = projection
        self.band_labels = band_labels

    def __repr__(self) -> str:

        return f'Image - Shape: {self.width}x{self.height}x{self.band_count} | EPSG: {self.epsg}'

    def __getitem__(self, band) -> "Image":

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

        return Image(image, self.geotransform, self.projection, band_labels=band_labels)

    def _get_band_by_number(self, band_number: int) -> np.ndarray:

        return self.pixels[:, :, band_number-1]

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
    def shape(self) -> Tuple[int]:

        return self.pixels.shape

    @property
    def dtype(self) -> str:

        return self.pixels.dtype

    @property
    def epsg(self) -> int:

        spatial_reference = osr.SpatialReference(wkt=self.projection)
        return spatial_reference.GetAttrValue("AUTHORITY", 1)

    def subset(self, x: int, y: int, width: int, height: int = None) -> "Image":

        if height is None:
            height = width
        pixels = self.pixels[y:y+height, x:x+width]
        geotransform = gis.subset_geotransform(self.geotransform, x, y)
        return Image(pixels, geotransform, self.projection, band_labels=self.band_labels)

    def clip_with(self, polygon: Polygon, mask_value: float = np.nan) -> "Image":

        return gis.clip_image(self, polygon, mask_value=mask_value)

    def upsample(self, factor: int) -> "Image":

        resampled_pixels = ndimage.zoom(self.pixels, factor, order=0)
        scaled_geotransform = self.geotransform.scale(factor)

        return Image(resampled_pixels, scaled_geotransform, self.projection, band_labels=self.band_labels)

    @staticmethod
    def stack(images: List["Image"]) -> "Image":

        if len(images) == 1:
            raise UserWarning("Only one image has been provided")
        else:
            stack = np.zeros((images[0].width, images[0].height, len(images)))

            for i, image in tqdm(enumerate(images), total=len(images), desc='Stacking bands'):
                stack[:, :, i] = image.pixels

            band_labels = {list(image.band_labels)[0]: i+1 for i, image in enumerate(images)
                           if image.band_labels is not None}
            return Image(stack, images[0].geotransform, images[0].projection, band_labels=band_labels)

    def save(self, filepath: str, data_type: str='uint16'):

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
    def _get_gdal_data_type(name: str):
        if name == 'uint8':
            return gdal.GDT_Byte
        elif name == 'uint16':
            return gdal.GDT_UInt16
        elif name == 'float32':
            return gdal.GDT_Float32
        else:
            raise UserWarning("Unrecognised data type.")
