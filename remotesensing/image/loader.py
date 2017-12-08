from remotesensing.image import Image
from remotesensing.image import Geotransform
from remotesensing.tools import gis

from osgeo import gdal, osr


class Loader:
    def load(self, filepath, band_labels=None, extent=None):
        """
        :type filepath: str
        :type band_labels: dict{str: int}
        :type extent: shapely.geometry.Polygon
        :rtype: image.Image
        """

        if extent:
            return self.load_from_dataset_and_clip(gdal.Open(filepath), band_labels, extent)
        else:
            return self.load_from_dataset(gdal.Open(filepath), band_labels)

    def load_from_dataset_and_clip(self, image_dataset, band_labels, extent):
        """
        :type image_dataset: osgeo.gdal.Dataset
        :type band_labels: dict
        :type extent: shapely.geometry.Polygon
        :rtype: remotesensing.image.image.Image
        """
        geotransform = Geotransform(image_dataset.GetGeoTransform())
        projection = image_dataset.GetProjection()
        epsg = osr.SpatialReference(wkt=projection).GetAttrValue("AUTHORITY", 1)
        pixel_polygon = gis.polygon_to_pixel(gis.transform_polygon(extent, in_epsg=4326, out_epsg=epsg), geotransform)

        bounds = [int(bound) for bound in pixel_polygon.bounds]

        pixels = image_dataset.ReadAsArray(bounds[0], bounds[2], bounds[1]-bounds[0], bounds[3]-bounds[2])
        geotransform = gis.subset_geotransform(geotransform, bounds[0], bounds[2])

        if pixels.ndim > 2:
            pixels = pixels.transpose(1, 2, 0)

        return Image(pixels, geotransform, projection, band_labels=band_labels)

    def load_from_dataset(self, image_dataset, band_labels=None):
        """
        :type image_dataset: osgeo.gdal.Dataset
        :type band_labels: dict
        :rtype: remotesensing.image.image.Image
        """
        geotransform = Geotransform(image_dataset.GetGeoTransform())
        projection = image_dataset.GetProjection()
        pixels = image_dataset.ReadAsArray()

        if pixels.ndim > 2:
            pixels = pixels.transpose(1, 2, 0)

        return Image(pixels, geotransform, projection, band_labels=band_labels)
