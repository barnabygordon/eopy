import numpy as np
from scipy import ndimage
from typing import List, Tuple, Optional
from scipy.ndimage.filters import gaussian_filter
from osgeo import gdal
from pyproj import CRS
from pyproj.exceptions import ProjError
from PIL import Image as PILImage
from PIL import ImageDraw
from shapely.geometry import Polygon

from remotesensing.image import Geotransform
from remotesensing.geometry import GeoPolygon

GTIFF_DRIVER = 'GTiff'


class Image:
    """ A generic image object using gdal with shape (y, x, band) """
    def __init__(self, pixels: np.ndarray, geotransform: Optional[Geotransform] = Geotransform.empty(), epsg: Optional[int] = None, no_data_value: float = 0.):

        self.pixels = pixels
        self.geotransform = geotransform
        try:
            self.crs = CRS.from_epsg(epsg)
        except ProjError:
            self.crs = None
        self.no_data_value = no_data_value
        self._index = 0

    def __repr__(self) -> str:

        return f'Image - Shape: {self.height}x{self.width}x{self.band_count} | EPSG: {self.epsg}'

    def __getitem__(self, image_slice) -> "Image":

        geo_transform = self.geotransform

        if type(image_slice) is tuple:
            pixels = self.pixels[image_slice]

            if len(image_slice) > 1:
                x, y = image_slice[1].start, image_slice[0].start
                if x is None:
                    x = 0
                if y is None:
                    y = 0
                geo_transform = self.geotransform.subset(x, y)

            return Image(pixels, geo_transform, self.epsg, self.no_data_value)

    def __next__(self):

        if self._index < self.band_count:
            if self.band_count == 1:
                band = self
            else:
                band = self[:, :, self._index]
            self._index += 1
            return band
        self._index = 0
        raise StopIteration

    def __iter__(self):
        return self

    @property
    def width(self) -> int:

        return self.pixels.shape[1]

    @property
    def height(self) -> int:

        return self.pixels.shape[0]

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
    def epsg(self) -> Optional[int]:

        if self.crs:
            return self.crs.to_epsg()

    @property
    def footprint(self) -> GeoPolygon:

        return GeoPolygon(Polygon([
            (self.geotransform.upper_left_x, self.geotransform.upper_left_y),
            (self.geotransform.upper_left_x + (self.width * self.geotransform.pixel_width),
             self.geotransform.upper_left_y),
            (self.geotransform.upper_left_x + (self.width * self.geotransform.pixel_width),
             self.geotransform.upper_left_y - (self.height * self.geotransform.pixel_height)),
            (self.geotransform.upper_left_x,
             self.geotransform.upper_left_y - (self.height * self.geotransform.pixel_height)),
            (self.geotransform.upper_left_x, self.geotransform.upper_left_y)
        ]), epsg=self.epsg)

    def clip_with(self, polygon: GeoPolygon, mask_value: float = np.nan) -> "Image":

        if str(polygon.epsg) != str(self.epsg):
            print(f'Image and polygon do not have the same EPSG: {self.epsg}, {polygon.epsg}')  # Todo: turn into log message

        bounds = [int(value) for value in polygon.polygon.bounds]
        mask = PILImage.new("L", (self.width, self.height), 1)

        [ImageDraw.Draw(mask).polygon(coordinates, 0) for coordinates in polygon.coordinates]
        mask_pixels = np.array(mask)
        mask_pixels = mask_pixels[bounds[1]:bounds[3], bounds[0]:bounds[2]]

        x, y = bounds[0], bounds[1]
        width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]

        subset = self[y:y + height, x:x + width]

        subset.pixels = np.copy(subset.pixels)
        subset.pixels[mask_pixels != 0] = mask_value

        return subset

    def upsample(self, factor: int) -> "Image":

        resampled_pixels = ndimage.zoom(self.pixels, factor, order=0)
        scaled_geo_transform = self.geotransform.scale(factor)

        return Image(resampled_pixels, scaled_geo_transform, self.epsg, self.no_data_value)

    def smooth(self, sigma: int = 5) -> "Image":

        return self.apply(lambda x: gaussian_filter(x, sigma=sigma))

    def apply(self, function: callable) -> "Image":

        modified_pixels = function(np.copy(self.pixels))
        return Image(modified_pixels, self.geotransform, self.epsg, self.no_data_value)

    @staticmethod
    def stack(images: List["Image"]) -> "Image":

        if len(images) == 1:
            raise UserWarning("Only one image has been provided")
        else:
            stack = np.zeros((images[0].height, images[0].width, sum([image.band_count for image in images])), dtype=images[0].dtype)

            band_count = 0
            for image in images:
                if image.band_count > 1:
                    for i in range(image.band_count):
                        stack[:, :, band_count] = image[:, :, i].pixels
                else:
                    stack[:, :, band_count] = image.pixels
                band_count += 1

            return Image(stack, images[0].geotransform, images[0].epsg, images[0].no_data_value)

    def save(self, file_path: str, data_type: Optional[str] = None):

        if not data_type:
            data_type = str(self.dtype)

        gdal_data_type = self._get_gdal_data_type(data_type)
        out_image = gdal.GetDriverByName(GTIFF_DRIVER)\
            .Create(file_path, self.width, self.height, self.band_count, gdal_data_type)
        out_image.SetGeoTransform(self.geotransform.tuple)
        if self.crs:
            out_image.SetProjection(self.crs.to_wkt())

        if self.band_count > 1:
            for band in range(self.band_count):
                out_image.GetRasterBand(band+1).WriteArray(self.pixels[:, :, band])
                if self.no_data_value is not None:
                    out_image.GetRasterBand(band+1).SetNoDataValue(float(self.no_data_value))

        else:
            out_image.GetRasterBand(1).WriteArray(self.pixels)
            if self.no_data_value is not None:
                out_image.GetRasterBand(1).SetNoDataValue(self.no_data_value)

        out_image.FlushCache()

    def normalise(self, output_range: Tuple[float, float] = (0, 1), current_range: Tuple[float, float] = None) -> "Image":

        if not current_range:
            current_range = (np.nanmin(self.pixels), np.nanmax(self.pixels))

        delta1 = current_range[1] - current_range[0]
        delta2 = output_range[1] - output_range[0]

        return self.apply(lambda x: (delta2 * (x - current_range[0]) / delta1) + output_range[0])

    def add_index(self, band_1: int, band_2: int) -> "Image":

        if self.band_count == 1:
            raise UserWarning(f'Image only has one band')

        for band in [band_1, band_2]:
            if self.band_count < band:
                raise UserWarning(f'Band number: {band} greater than image bands: {self.band_count}')

        band_1_pixels = self.pixels[:, :, band_1]
        band_2_pixels = self.pixels[:, :, band_2]

        index = (band_1_pixels - band_2_pixels) / (band_1_pixels + band_2_pixels)

        return Image(np.dstack([self.pixels, index]), self.geotransform, self.epsg, self.no_data_value)

    def mask(self, value: float = None) -> "Image":

        if not value:
            value = self.no_data_value

        image = self.apply(lambda x: x)
        image.pixels[image.pixels == value] = np.nan

        return image

    def unmask(self, value: float = None) -> "Image":

        if not value:
            value = self.no_data_value

        image = self.apply(lambda x: x)
        image.pixels[np.isnan(image.pixels)] = value

        return image

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
