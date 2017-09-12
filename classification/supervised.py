from image import Image
from tools import gis

import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from sklearn.ensemble import RandomForestClassifier


class Supervised:
    """ A pixel-based classifier that uses the RandomForest model
        :param image: Image
        :param vector_filepath: Path to shapefile
        :param label_name: Column name of labels
        :param model: Type of model to be trained
        :param estimators: Number of estimators
    """
    def __init__(self,
                 image: Image,
                 vector_filepath: str,
                 label_name: str='class',
                 model=RandomForestClassifier,
                 estimators: int=100):
        self.image = image
        self.vectors = self._gather_data(vector_filepath)
        self.label_name = label_name
        self.model = model(estimators)
        self.trained = False

    def _gather_data(self, vector_filepath: str) -> gpd.GeoDataFrame:
        """ Extract all features for class vectors """
        gdf = gpd.read_file(vector_filepath)
        gdf['pixel_polygon'] = gdf.geometry.apply(lambda x: gis.polygon_to_pixel(x, self.image.geotransform))
        gdf['features'] = gdf.pixel_polygon.apply(lambda x: self._extract_features(x))

        return gdf

    def _extract_features(self, polygon: Polygon) -> np.ndarray:
        """ Extract all features and remove nan values """
        clipped_image = self.image.clip_with(polygon)
        features = clipped_image.pixels.reshape((clipped_image.width * clipped_image.height, clipped_image.band_count))
        clean_features = np.array([feature for feature in features if not np.isnan(feature.min())])

        return clean_features

    def plot_features(self):
        """ Plot the averages of all class features and their variance """
        plt.figure(figsize=(15, 10))

        for c in self.vectors[self.label_name].unique():
            all_features = np.vstack(self.vectors.loc[self.vectors[self.label_name] == c].features.tolist())

            mean_feature = np.mean(all_features, axis=0)
            variance = np.var(all_features, axis=0)

            plt.plot(mean_feature, label=c)
            plt.fill_between(np.arange(len(mean_feature)), mean_feature - variance, mean_feature + variance, alpha=0.6)

        plt.legend()
        plt.show()

    def train_model(self) -> None:
        """ Train the model """
        labels, features = [], []

        for c in self.vectors[self.label_name].unique():
            all_features = np.vstack(self.vectors.loc[self.vectors[self.label_name] == c].features.tolist())

            features.extend(all_features)
            labels.extend([self.vectors[self.label_name].unique().tolist().index(c)] * len(all_features))

        self.model.fit(features, labels)
        self.trained = True

    def test_model(self, image: Image) -> Image:
        """ Run the trained model on an image """
        if not self.trained:
            raise UserWarning("Model needs to be trained before it can be tested.")
        features = image.pixels.reshape(image.width * image.height, image.band_count)
        features[np.isnan(features)] = 0

        results_list = self.model.predict(features)
        results_image = results_list.reshape(image.width, image.height)
        results_image[image[0].pixels == np.nan] = 0.

        return Image(results_image, self.image.geotransform, self.image.projection)
