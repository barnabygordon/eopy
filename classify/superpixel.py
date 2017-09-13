from skimage.segmentation import slic
from sklearn.cluster import KMeans
import geopandas as gpd
import numpy as np

from image import Image
from image.geotransform import Geotransform
from tools import gis


class Superpixels:
    """ A class to segment an image into superpixels for classification """
    def __init__(self, gdf: gpd.GeoDataFrame, geotransform: Geotransform, epsg: int, number_of_features: int):
        self.gdf = gdf
        self.geotransform = geotransform
        self.epsg = epsg
        self.number_of_features = number_of_features

    @classmethod
    def segment_image(cls,
                      image: Image,
                      extract_values: bool=True,
                      n_segments: int=100,
                      compactness: float=10.,
                      sigma: int=0,
                      enforce_connectivity: bool=True) -> "Superpixels":
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
            superpixel_list.append(gis.vectorise_image(segment, levels=[0.9, 1.1]).iloc[0].geom)

        gdf = gpd.GeoDataFrame(geometry=superpixel_list)

        image.pixels = np.copy(image.pixels).astype(float)
        if extract_values:
            if multichannel:
                gdf['features'] = gdf.geometry.apply(lambda x: np.nanmean(image.clip_with(x).pixels, axis=(0, 1)))
            else:
                gdf['features'] = gdf.geometry.apply(lambda x: np.nanmean(image.clip_with(x).pixels))

        return Superpixels(gdf, image.geotransform, image.epsg, number_of_features=image.band_count)

    def cluster(self, n_clusters: int=2) -> None:
        if self.number_of_features == 1:
            features = [[feature] for feature in self.gdf.features.tolist()]
        else:
            features = self.gdf.features.tolist()
        self.gdf['cluster'] = KMeans(n_clusters=n_clusters).fit_predict(features)

    def save(self, filename: str, driver: str='GeoJSON'):
        gdf = self.gdf.drop('geometry', axis=1)
        gdf.to_file(filename, driver=driver)

    def project_to_geographic(self):
        self.gdf['geographic'] = self.gdf.geometry.apply(
            lambda x: gis.polygon_to_world(x, self.geotransform))
        self.gdf = self.gdf.set_geometry('geographic')
