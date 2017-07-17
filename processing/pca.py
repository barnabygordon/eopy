from sklearn.decomposition import PCA
import pandas as pd
import numpy as np


class ImagePCA:
    """ Principal Components Analysis """
    @staticmethod
    def calculate(image: np.ndarray, band_names: [str]=None) -> (np.ndarray, pd.DataFrame):
        """ Calculate PCs for each image band
        :param image: An image array of shape: (rows, columns, bands)
        :param band_names: List of band names to be shown in eigenvector output
        :return: The PCs of the image array with the same shape as well as a dataframe of the eigenvectors
        """
        pca = PCA(n_components=image.shape[2])

        x = image.reshape(-1, image.shape[2])
        pca.fit(x)

        eigenvectors = pca.components_
        scores = pca.transform(x)
        result = scores.reshape(image.shape)

        eigenvectors = pd.DataFrame(eigenvectors)
        eigenvectors.columns = ["PC {}".format(i+1) for i in range(image.shape[2])]

        if band_names is not None:
            assert len(band_names) == image.shape[2], "Band names don't match with image shape"
            eigenvectors.index = band_names
        else:
            eigenvectors.index = ["Band {}".format(i+1) for i in range(image.shape[2])]

        return result, eigenvectors
