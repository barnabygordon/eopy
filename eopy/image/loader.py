from eopy.image import Image
from eopy.image import Geotransform
from eopy.geometry import GeoPolygon

from typing import Optional
from pyproj import CRS
from pyproj.exceptions import CRSError
from osgeo import gdal


class Loader:

    def load(self, file_path: str, extent: GeoPolygon = None) -> Image:

        if extent:
            return self.load_from_dataset_and_clip(gdal.Open(file_path), extent)
        else:
            return self.load_from_dataset(gdal.Open(file_path))

    def load_from_dataset_and_clip(self, image_dataset: gdal.Dataset, extent: GeoPolygon) -> Image:

        geo_transform = self._load_geotransform(image_dataset)
        pixel_polygon = extent.to_pixel(geo_transform)

        bounds = [int(bound) for bound in pixel_polygon.polygon.bounds]

        pixels = image_dataset.ReadAsArray(bounds[0], bounds[1], bounds[2]-bounds[0], bounds[3]-bounds[1])

        if pixels is None:
            raise UserWarning(f'Unable to open image with extent: {bounds}')

        subset_geo_transform = geo_transform.subset(x=bounds[0], y=bounds[1])
        pixel_polygon = extent.to_pixel(subset_geo_transform)

        if pixels.ndim > 2:
            pixels = pixels.transpose(1, 2, 0)

        no_data_value = self._get_no_data_value(image_dataset)
        try:
            epsg = CRS.from_wkt(image_dataset.GetProjection()).to_epsg()
        except CRSError:
            epsg = None

        return Image(pixels, subset_geo_transform, epsg, no_data_value).clip_with(pixel_polygon, mask_value=0)

    def load_from_dataset(self, image_dataset: gdal.Dataset) -> Image:

        geo_transform = self._load_geotransform(image_dataset)
        try:
            epsg = CRS.from_wkt(image_dataset.GetProjection()).to_epsg()
        except CRSError:
            epsg = None
        pixels = image_dataset.ReadAsArray()

        if pixels.ndim > 2:
            pixels = pixels.transpose(1, 2, 0)

        no_data_value = self._get_no_data_value(image_dataset)

        return Image(pixels, geo_transform, epsg, no_data_value)

    def _load_geotransform(self, image_dataset: gdal.Dataset) -> Geotransform:

        return Geotransform.from_tuple(image_dataset.GetGeoTransform())

    def _get_no_data_value(self, image_dataset: gdal.Dataset) -> Optional[float]:

        return image_dataset.GetRasterBand(1).GetNoDataValue()
