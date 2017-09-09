import numpy as np

from image import Image


class DDS:
    """ Direct Decorrelation Stretch """
    @staticmethod
    def calculate(image: Image, k: float=0.6) -> Image:
        """ Saturates an image according to the k factor
        :param image: A 3D image with 3 bands and shape (columns, rows, bands)
        :param k: The factor to which the image should be saturated
        :return: A saturated image
        """
        x = np.amin(image.pixels, axis=0)

        dds_image = np.copy(image.pixels)
        for i in range(image.band_count):
            dds_image[:, :, i] -= (k * x)

        return Image(dds_image, image.geotransform, image.projection,
                     band_labels=image.band_labels, metadata=image.metadata)
