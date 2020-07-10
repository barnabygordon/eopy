import numpy as np

from remotesensing.image import Image


class DDS:
    """ Direct Decorrelation Stretch """
    @staticmethod
    def calculate(image: Image, k: float = 0.6) -> Image:

        x = np.amin(image.pixels, axis=2)

        return image.stack([band.apply(lambda i: i - (k * x)) for band in image])
