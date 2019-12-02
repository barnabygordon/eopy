import numpy as np

from remotesensing.image import Image


class DDS:
    """ Direct Decorrelation Stretch """
    @staticmethod
    def calculate(image: Image, k: float = 0.6) -> Image:

        x = np.amin(image.pixels, axis=2)

        dds_image = np.copy(image.pixels)
        for i in range(image.band_count):
            dds_image[:, :, i] -= (k * x)

        return Image(dds_image, image.geotransform, image.projection)
