import numpy as np

from image import Image


class DDS:
    """ Direct Decorrelation Stretch """
    @staticmethod
    def calculate(image, k=0.6):
        """ Saturates an image according to the k factor
        :type image: image.Image
        :type k: float
        :rtype: image.Image
        """
        x = np.amin(image.pixels, axis=0)

        dds_image = np.copy(image.pixels)
        for i in range(image.band_count):
            dds_image[:, :, i] -= (k * x)

        return Image(dds_image, image.geotransform, image.projection,
                     band_labels=image.band_labels, metadata=image.metadata)
