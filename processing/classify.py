from image import Image
from tools import gis

import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier


class Classifier:
    """ A Random Forest-based pixel-by-pixel classifer that requires a shapefile delineating classes"""
    def __init__(self, image: Image, class_data_filepath: str, class_name: str='label', n_estimators: int=100):
        """
        :param image: An image object with n-number of bands
        :param class_data_filepath: Path to the shapefile/geojson
        :param class_name: name used for class attribution
        :param n_estimators: number of estimators to be used in the Random Forest
        """
        self.image = image
        self.class_data = self._open_class_file(class_data_filepath)
        self.classifier = RandomForestClassifier(n_estimators=n_estimators)
        self.class_name = class_name

    def _open_class_file(self, filepath: str) -> gpd.GeoDataFrame:
        class_data = gpd.read_file(filepath)

        class_data.geometry = class_data.geometry.apply(
            lambda x: gis.polygon_to_pixel(x,
                                           self.image.geotransform,
                                           self.image.height))

        return class_data

    def train(self) -> None:
        """ Train the model using the image data and labels """
        classes, class_values = [], []
        features = []
        for i, row in self.class_data.iterrows():
            clip = gis.clip_image(self.image.pixels, row.geometry)
            flat_clip = clip.reshape(clip.shape[0] * clip.shape[1], clip.shape[2])
            clean_features = [features for features in flat_clip if not np.isnan(np.sum(features))]

            features.extend(clean_features)

            if row[self.class_name] not in classes:
                classes.append(row[self.class_name])

            class_value = classes.index(row[self.class_name])
            class_values.extend([class_value] * len(clean_features))

        self.classifier.fit(features, class_values)

    def predict(self, test_image=np.ndarray) -> np.ndarray:
        """ Use the trained model to classify an image
        :param test_image: An array that must have the same number of bands as the input
        :return: A 2D array with integer values representing the classes
        """
        assert (test_image.shape[2] == self.image.band_count, "Train and test images must have same band count.")
        test_data = test_image.reshape(-1, self.image.band_count)
        predictions = self.classifier.predict(test_data)

        # TODO: return class lookup table
        return predictions.reshape((test_image.shape[0], test_image.shape[1]))

    def show(self, figsize: (int, int)=(15, 10)):
        """ Plot the image data with the labels overlain """
        f, ax = plt.subplots(figsize=figsize)

        ax.imshow(self.image.pixels[:, :, 0])
        self.class_data.plot(ax=ax, column='label', legend=True)
        plt.show()
