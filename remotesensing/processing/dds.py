import numpy as np

from remotesensing.image import Image


class DDS:
    """ Direct Decorrelation Stretch """
    @staticmethod
    def calculate(image: Image, k: float = 0.6) -> Image:

        x = np.amin(image.pixels, axis=2)

        bands = []
        for band_number in range(image.band_count):
            bands.append(image[:, :, band_number].apply(lambda i: i - (k * x)))

        return image.stack(bands)
