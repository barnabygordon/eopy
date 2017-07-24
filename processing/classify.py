from image import Image
from tools import gis

import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier


class Classifier:
    """ A Random Forest-based pixel-by-pixel classifer that requires a shapefile delineating classes"""
    def __init__(self, image: Image, classifier=RandomForestClassifier, n_estimators=100):
        """
        :param image: An image object with n-number of bands
        :param n_estimators: number of estimators to be used in the Random Forest
        """
        self.image = image
        self.classifier = classifier(n_estimators)
        self.trained = False

    def _open_class_file(self, filepath: str) -> gpd.GeoDataFrame:
        """ Open a shapefile and return a geopandas dataframe """
        class_data = gpd.read_file(filepath)

        class_data.geometry = class_data.geometry.apply(
            lambda x: gis.polygon_to_pixel(x, self.image.geotransform))

        return class_data

    def train(self, class_data_filepath: str, class_name: str='label') -> None:
        """ Train a model using a shapefile as labelled class data
        :param class_data_filepath: Path to the shapefile containing class polygons
        :param class_name: Name of the attribute column
        """
        class_data = self._open_class_file(class_data_filepath)

        classes, class_values = [], []
        features = []
        for i, row in class_data.iterrows():
            clip = gis.clip_image(self.image.pixels, row.geometry)
            flat_clip = clip.reshape(clip.shape[0] * clip.shape[1], clip.shape[2])
            clean_features = [features for features in flat_clip if not np.isnan(np.sum(features))]

            features.extend(clean_features)

            if row[class_name] not in classes:
                classes.append(row[class_name])

            class_value = classes.index(row[class_name])
            class_values.extend([class_value] * len(clean_features))

        self.classifier.fit(features, class_values)
        self.trained = True

    def predict(self, test_image: np.array) -> np.ndarray:
        """ Use the trained model to classify an image
        :param test_image: An array that must have the same number of bands as the input
        :return: A 2D array with integer values representing the classes
        """
        assert (self.trained is True, "Model must first be trained.")
        assert (test_image.shape[2] == self.image.band_count, "Train and test images must have same band count.")
        test_data = test_image.reshape(-1, self.image.band_count)
        predictions = self.classifier.predict(test_data)

        # TODO: return class lookup table
        return predictions.reshape((test_image.shape[0], test_image.shape[1]))

    def show(self, class_file_path: str, figsize: (int, int)=(15, 10)):
        """ Plot the image data with the labels overlain """
        f, ax = plt.subplots(figsize=figsize)

        ax.imshow(self.image.pixels[:, :, 0])
        self._open_class_file(class_file_path).plot(ax=ax, column='label', legend=True)
        plt.show()
