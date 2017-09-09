from scipy.ndimage.filters import gaussian_filter
from cv2 import resize
from tqdm import tqdm
import numpy as np

from image import Image


class SFIM:
    """ (Smoothing Filter-Based Intensity Modulation)
    A class for fusing together images for pansharpening
    """
    @classmethod
    def calculate(cls, low_resolution_image: Image, pan_image: Image) -> Image:
        """ Fuse a low resolution image with a higher resolution one
        :param low_resolution_image: An array with shapes of either (rows, cols) or (rows, cols, bands)
        :param pan_image: A 2D array that is 2x the size of the lower resolution image
        :return: An array the same shape as the pan_image but with the same number of bands as the lower resolution
        """

        pan_smooth = cls._smooth_image(pan_image.pixels)

        if low_resolution_image.band_count > 2:
            pansharpened = np.zeros((
                pan_image.shape[0],
                pan_image.shape[1],
                low_resolution_image.shape[2]))

            for b in tqdm(range(pansharpened.shape[2]), total=pansharpened.shape[2], desc="Fusing images"):
                pansharpened[:, :, b] = cls._fuse_images(
                    low_resolution_image=low_resolution_image[b].pixels,
                    pan_image=pan_image.pixels,
                    smoothed_pan_image=pan_smooth)

        else:
            pansharpened = cls._fuse_images(
                low_resolution_image=low_resolution_image.pixels,
                pan_image=pan_image.pixels,
                smoothed_pan_image=pan_smooth)

        return Image(pansharpened, pan_image.geotransform, pan_image.projection,
                     band_labels=low_resolution_image.band_labels, metadata=low_resolution_image.metadata)

    @staticmethod
    def _fuse_images(low_resolution_image: np.ndarray,
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
    def _smooth_image(image: Image, sigma: int=5) -> np.ndarray:
        """ Perform a gaussian filter on an image """
        return gaussian_filter(image.pixels, sigma=sigma)
