from image import Image
from tools import gis

import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier


class Classifier:
    def __init__(self, image: Image, class_data_filepath: str, n_estimators: int=100):
        self.image = image
        self.class_data = self._open_class_file(class_data_filepath)
        self.classifier = RandomForestClassifier(n_estimators=n_estimators)

    def _open_class_file(self, filepath: str) -> gpd.GeoDataFrame:
        class_data = gpd.read_file(filepath)

        class_data['pixel_polygon'] = class_data.geometry.apply(
            lambda x: gis.polygon_to_pixel(x,
                                           self.image.geotransform,
                                           self.image.height))
        class_data.set_geometry('pixel_polygon')

        return class_data

    def train(self) -> None:
        classes, class_values = [], []
        features = []
        for i, row in self.class_data.iterrows():
            clip = gis.clip_image(self.image.pixels, row.pixel_polygon)
            flat_clip = clip.reshape(clip.shape[0] * clip.shape[1], clip.shape[2])
            clean_features = [features for features in flat_clip if not np.isnan(np.sum(features))]

            features.extend(clean_features)

            if row.label not in classes:
                classes.append(row.label)

            class_value = classes.index(row.label)
            class_values.extend([class_value] * len(clean_features))

        self.classifier.fit(features, class_values)

    def predict(self) -> np.ndarray:
        test_data = self.image.pixels.reshape(-1, self.image.band_count)
        predictions = self.classifier.predict(test_data)

        return predictions.reshape((self.image.height, self.image.width))

    def show(self, figsize: (int, int)=(15, 10)):
        f, ax = plt.subplots(figsize=figsize)

        ax.imshow(self.image.pixels[:, :, 0])
        self.class_data.plot(ax=ax, column='label', legend=True)
        plt.show()
