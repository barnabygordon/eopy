import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image as PILImage
from PIL import ImageDraw
from sklearn import metrics
from typing import List
from sklearn.ensemble import RandomForestClassifier

from eopy.image import Image
from eopy.geometry import GeoPolygon


class Supervised:

    def __init__(
            self,
            image: Image,
            epsg: int,
            vector_filepath: str,
            label_name: str = 'class',
            model=RandomForestClassifier,
            estimators: int = 100):

        self.image = image
        self.vectors = self._gather_data(vector_filepath, epsg)
        self.label_name = label_name
        self.model = model(estimators)
        self.trained = False

    def _gather_data(self, vector_filepath: str, epsg: int) -> gpd.GeoDataFrame:

        gdf = gpd.read_file(vector_filepath)
        gdf['pixel_polygon'] = gdf.geometry.apply(lambda x: GeoPolygon(x, epsg).to_pixel(self.image.geotransform))
        gdf['features'] = gdf.pixel_polygon.apply(lambda x: self._extract_features(x))
        gdf = gdf.set_geometry('pixel_polygon')

        return gdf

    def _extract_features(self, polygon: GeoPolygon) -> np.ndarray:

        clipped_image = self.image.clip_with(polygon)
        features = clipped_image.pixels.reshape((clipped_image.width * clipped_image.height, clipped_image.band_count))
        clean_features = np.array([feature for feature in features if not np.isnan(feature.min())])

        return clean_features

    def train_model(self):
        """ Train the model """
        labels, features = [], []

        for c in self.vectors[self.label_name].unique():
            all_features = np.vstack(self.vectors.loc[self.vectors[self.label_name] == c].features.tolist())

            features.extend(all_features)
            class_value = self.vectors[self.label_name].unique().tolist().index(c)
            labels.extend([class_value] * len(all_features))

        self.model.fit(features, labels)
        self.trained = True

    def apply_model(self, image: Image) -> Image:

        if not self.trained:
            raise UserWarning("Model needs to be trained before it can be tested.")
        features = image.pixels.reshape(image.width * image.height, image.band_count)
        features[np.isnan(features)] = 0

        results_list = self.model.predict(features)
        results_image = results_list.reshape(image.width, image.height)
        results_image[np.isnan(image[0].pixels)] = 0.

        return Image(results_image, self.image.geotransform, self.image.projection, self.image.no_data_value)

    def test_model(self, output_image: Image, truth_vectors: gpd.GeoDataFrame):

        truth_image = PILImage.new("L", (output_image.height, output_image.width), 200)
        for i, row in truth_vectors.iterrows():
            class_value = truth_vectors[self.label_name].unique().tolist().index(row[self.label_name])
            polygon = list(row['pixel_polygon'].exterior.coords)

            ImageDraw.Draw(truth_image).polygon(polygon, class_value)
        truth_image = np.array(truth_image).astype('float')

        truth = truth_image[truth_image != 200]
        predictions = output_image.pixels[truth_image != 200]
        confusion_matrix = metrics.confusion_matrix(truth, predictions)

        self._plot_confusion_matrix(confusion_matrix)

    def plot_features(self, ylabel: str = None, xticks: List[str] = None):
        """ Plot the averages of all class features and their variance """
        plt.figure(figsize=(15, 10))

        for c in self.vectors[self.label_name].unique():
            all_features = np.vstack(self.vectors.loc[self.vectors[self.label_name] == c].features.tolist())

            mean_feature = np.mean(all_features, axis=0)
            variance = np.std(all_features, axis=0)

            plt.fill_between(np.arange(len(mean_feature)), mean_feature - variance, mean_feature + variance, alpha=0.1)
            plt.plot(mean_feature, label=c)

        if ylabel:
            plt.ylabel(ylabel, fontsize=20)
        if xticks:
            plt.xticks(np.arange(len(xticks)), xticks, rotation=45, fontsize=15)
        plt.legend()
        plt.show()

    def plot_vectors(self, image: np.ndarray):

        f, ax = plt.subplots(figsize=(15, 10))
        ax.imshow(image)
        self.vectors.plot(column=self.label_name, ax=ax, legend=True, linewidth=0.1)
        plt.show()

    def _plot_confusion_matrix(self, confusion_matrix: np.ndarray, cmap: str = 'OrRd'):
        plt.figure(figsize=(15, 10))
        plt.imshow(confusion_matrix, cmap=cmap)

        classes = self.vectors[self.label_name].unique().tolist()
        tick_marks = np.arange(len(classes))

        plt.xticks(tick_marks, classes, rotation=45)
        plt.yticks(tick_marks, classes)

        for i in range(confusion_matrix.shape[0]):
            for j in range(confusion_matrix.shape[1]):
                plt.text(j, i, confusion_matrix[i, j], horizontalalignment='center')

        plt.tight_layout()
        plt.ylabel('Observed', fontsize=20)
        plt.xlabel('Predicted', fontsize=20)
        plt.show()
