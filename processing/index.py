from image import Image
import warnings


class IndexCalculator:
    @staticmethod
    def check_bands_exist(image, band_list):
        missing_bands = [band for band in band_list if band not in image.band_labels]

        if len(missing_bands) > 0:
            raise UserWarning("Image is missing bands: {}".format(', '.join(missing_bands)))

    @staticmethod
    def save_divide(numerator, denominator):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return numerator / denominator


class Landsat8(IndexCalculator):
    @classmethod
    def iron_oxide(cls, image):
        IndexCalculator.check_bands_exist(image, ['red', 'blue'])
        red = image[image.band_labels['red']-1].pixels
        blue = image[image.band_labels['blue']-1].pixels

        iron_oxide = IndexCalculator.save_divide(red, blue)
        return Image(iron_oxide, image.geotransform, image.projection,
                     band_labels={'iron_oxide': 1}, metadata=image.metadata)
