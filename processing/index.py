from image import Image
import warnings


class IndexCalculator:
    @staticmethod
    def check_bands_exist(image, band_list):
        missing_bands = [band for band in band_list if band not in image.band_labels]

        if len(missing_bands) > 0:
            raise UserWarning("Image is missing bands: {}".format(', '.join(missing_bands)))

    @staticmethod
    def safe_divide(numerator, denominator):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return numerator / denominator


class Landsat8(IndexCalculator):
    @classmethod
    def iron_oxide(cls, image):
        IndexCalculator.check_bands_exist(image, ['red', 'blue'])
        red = image['red'].pixels
        blue = image['blue'].pixels

        iron_oxide = IndexCalculator.safe_divide(red, blue)
        return Image(iron_oxide, image.geotransform, image.projection,
                     band_labels={'iron_oxide': 1}, metadata=image.metadata)

    @classmethod
    def clay(cls, image):
        IndexCalculator.check_bands_exist(image, ['swir_1', 'swir_2'])
        swir_1 = image['swir_1'].pixels
        swir_2 = image['swir_2'].pixels

        clay = IndexCalculator.safe_divide(swir_2, swir_1)
        return Image(clay, image.geotransform, image.projection,
                     band_labels={'clay': 1}, metadata=image.metadata)

    @classmethod
    def ndvi(cls, image):
        IndexCalculator.check_bands_exist(image, ['nir', 'red'])
        nir = image['nir'].pixels
        red = image['red'].pixels

        ndvi = IndexCalculator.safe_divide((nir - red), (nir + red))
        return Image(ndvi, image.geotransform, image.projection,
                     band_labels={'ndvi': 1}, metadata=image.metadata)

