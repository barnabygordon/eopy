from sklearn.decomposition import PCA
import pandas as pd
import numpy as np
from typing import List, Tuple

from remotesensing.image import Image


class ImagePCA:
    """ Principal Components Analysis """
    @staticmethod
    def calculate(image: Image, band_names: List[str] = None) -> Tuple[np.ndarray, pd.DataFrame]:

        pca = PCA(n_components=image.shape[2])

        x = image.pixels.reshape(-1, image.shape[2])
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
