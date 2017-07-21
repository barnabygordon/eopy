import numpy as np


class DDS:
    """ Direct Decorrelation Stretch """
    @staticmethod
    def calculate(image: np.ndarray, k: float=0.6) -> np.ndarray:
        """ Saturates an image according to the k factor
        :param image: A 3D image with 3 bands and shape (columns, rows, bands)
        :param k: The factor to which the image should be saturated
        :return: A saturated image
        """
        r, g, b = image[:, :, 0], image[:, :, 1], image[:, :, 2]

        x = np.amin(image, axis=2)

        rk = r - (k*x)
        gk = g - (k*x)
        bk = b - (k*x)

        return np.dstack((rk, gk, bk))
