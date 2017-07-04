from osgeo import gdal
from scipy.ndimage.filters import gaussian_filter
from cv2 import resize

import numpy as np


class SFIM:
    def calculate(self, image_path: str, pan_path: str) -> np.ndarray:
        image_list = [pan_path, image_path]
        data = {}

        for i, image_path in enumerate(image_list):
            image_dataset = gdal.Open(image_path)
            image = image_dataset.ReadAsArray()
            data[i] = image

        pan = data[0]
        image = data[1]

        pan_smooth = self._smooth_image(pan)

        pansharpened = np.zeros((
            image.shape[0],
            pan.shape[0],
            pan.shape[1]))

        for b in range(image.shape[0]):
            band = resize(image[b, :, :], (pan.shape[1], pan.shape[0]))
            band = (band * pan) / pan_smooth
            pansharpened[b, :, :] = band

        return pansharpened.transpose(1, 2, 0)

    @staticmethod
    def _smooth_image(image: np.ndarray, sigma: int=5) -> np.ndarray:
        """ Perform a gaussian filter on an image """
        return gaussian_filter(image, sigma=sigma)