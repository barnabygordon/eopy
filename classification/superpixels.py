from skimage.segmentation import slic
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import geopandas as gpd

from image import Image


class Superpixels:
    def __init__(self, image: Image, n_segments: int=100, compactness: float=10.,
                 sigma: int=0, enforce_connectivity: bool=True):
        self.image = image.pixels
        self.geotransform = image.geotransform
        self.projection = image.projection
        self.epsg = image.epsg
        self.n_segments = n_segments
        self.compactness = compactness
        self.sigma = sigma
        self.enforce_connectivity = enforce_connectivity
        self.superpixels = self._extract_superpixels()

    def _extract_superpixels(self):
        if self.image.ndim > 2:
            multichannel = True
        else:
            multichannel = False
        segments = slic(self.image, n_segments=self.n_segments, compactness=self.compactness, sigma=self.sigma,
                        multichannel=multichannel, enforce_connectivity=self.enforce_connectivity)

        superpixel_list = []
        for i in range(segments.max()):
            segment = segments == i
            superpixel_list.append(self._vectorise_superpixel(segment))

        superpixels = gpd.GeoDataFrame(geometry=superpixel_list)

        return superpixels

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
