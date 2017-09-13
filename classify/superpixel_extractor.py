from skimage.segmentation import slic
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np

from image import Image
from image.geotransform import Geotransform
from classify.superpixels import Superpixels


class SuperpixelExtractor:
    """ A class to segment an image into superpixels for classification """
    def __init__(self, superpixels: gpd.GeoDataFrame, geotransform: Geotransform, epsg: int):
        self.superpixels = superpixels
        self.geotransform = geotransform
        self.epsg = epsg

    @classmethod
    def segment_image(cls,
                      image: Image,
                      extract_values: bool=True,
                      n_segments: int=100,
                      compactness: float=10.,
                      sigma: int=0,
                      enforce_connectivity: bool=True) -> Superpixels:
        """ Extract superpixels from an image
        :param image: An Image
        :param extract_values: Bool
        :param n_segments: Number of segments
        :param compactness: How square the segments should be
        :param sigma: How smooth the segments should be
        :param enforce_connectivity: Bool
        :return: Superpixels
        """
        if image.band_count > 2:
            multichannel = True
        else:
            multichannel = False
        segments = slic(image.pixels, n_segments=n_segments, compactness=compactness, sigma=sigma,
                        multichannel=multichannel, enforce_connectivity=enforce_connectivity)

        superpixel_list = []
        for i in range(segments.max()):
            segment = segments == i
            superpixel_list.append(cls._vectorise_superpixel(segment))

        superpixels = gpd.GeoDataFrame(geometry=superpixel_list)

        if extract_values:
            if image.band_count == 1:
                superpixels['band_1'] = superpixels.geometry.apply(lambda x: cls._extract_pixel_values(x, image))
            else:
                for i in range(image.band_count):
                    superpixels['band_{}'.format(i)] = superpixels.geometry.apply(
                        lambda x: cls._extract_pixel_values(x, image[i]))

        return Superpixels(superpixels, image.geotransform, image.epsg)

    @staticmethod
    def _vectorise_superpixel(segment):
        contour_collection = plt.contour(segment, levels=[0])
        plt.clf()

        contour_polygons = []
        for i, contour in enumerate(contour_collection.collections):
            for path in contour.get_paths():
                path.should_simplify = False
                polygon = path.to_polygons()

                holes, exterior = [], []
                if len(polygon) > 0 and len(polygon[0]) > 5:
                    exterior = polygon[0]
                    if len(polygon) > 1:
                        holes = [h for h in polygon[1:] if len(h) > 5]

                if len(exterior) > 5:
                    polygon = Polygon(exterior, holes)
                    contour_polygons.append(polygon)

        return contour_polygons[0]

    @staticmethod
    def _extract_pixel_values(superpixel: Polygon, image: Image) -> gpd.GeoDataFrame:
        clip_image = image.clip_with(superpixel)

        return np.nanmean(clip_image.pixels)
