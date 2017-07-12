from scipy.ndimage.filters import gaussian_filter
from cv2 import resize
import numpy as np


class SFIM:
    """ (Smoothing Filter-Based Intensity Modulation)
    A class for fusing together images for pansharpening
    """
    def calculate(self, low_resolution_image: np.ndarray, pan_image: np.ndarray) -> np.ndarray:
        """ Fuse a low resolution image with a higher resolution one
        :param low_resolution_image: An array with shapes of either (rows, cols) or (rows, cols, bands)
        :param pan_image: A 2D array that is 2x the size of the lower resolution image
        :return: An array the same shape as the pan_image but with the same number of bands as the lower resolution
        """

        pan_smooth = self._smooth_image(pan_image)

        if low_resolution_image.ndim > 2:
            pansharpened = np.zeros((
                pan_image.shape[0],
                pan_image.shape[1],
                low_resolution_image.shape[2]))

            for b in range(pansharpened.shape[2]):
                pansharpened[:, :, b] = self._fuse_images(
                    low_resolution_image=low_resolution_image[:, :, b],
                    pan_image=pan_image,
                    smoothed_pan_image=pan_smooth)

        else:
            pansharpened = self._fuse_images(
                low_resolution_image=low_resolution_image,
                pan_image=pan_image,
                smoothed_pan_image=pan_smooth)

        return pansharpened

    def _fuse_images(self,
                    low_resolution_image: np.ndarray,
                    pan_image: np.ndarray,
                    smoothed_pan_image: np.ndarray) -> np.ndarray:
        """ Fuse together two images of the same number of dimensions
        :param low_resolution_image: A 2D lower resolution image
        :param pan_image: A 2D higher resolution image
        :param smoothed_pan_image: The smoothed higher resolution image
        :return: Fused image
        """
        resized_image = resize(low_resolution_image, pan_image.shape[::-1])
        return (resized_image * pan_image) / smoothed_pan_image


    @staticmethod
    def _smooth_image(image: np.ndarray, sigma: int=5) -> np.ndarray:
        """ Perform a gaussian filter on an image """
        return gaussian_filter(image, sigma=sigma)
