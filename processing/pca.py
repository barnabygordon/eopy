from sklearn.decomposition import PCA
import pandas as pd
import numpy as np


class ImagePCA:
    """ Principal Components Analysis """
    @staticmethod
    def calculate(image: np.ndarray) -> (np.ndarray, pd.DataFrame):
        """ Calculate PCs for each image band
        :param image: An image array of shape: (rows, columns, bands)
        :return: The PCs of the image array with the same shape as well as a dataframe of the eigenvectors
        """
        pca = PCA(n_components=image.shape[2])

        x = image.reshape(-1, image.shape[2])
        pca.fit(x)

        eigenvectors = pca.components_
        scores = pca.transform(x)
        result = scores.reshape(image.shape)

        eigenvectors = pd.DataFrame(eigenvectors)

        return result, eigenvectors
