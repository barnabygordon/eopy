import math
from urllib.request import urlopen

import numpy as np

from image import Image
from image.sensor import Landsat8


class Calibration:
    """ Functionality to calibrate satellite data """
    def __init__(self, metadata_url):
        """
        :type metadata_url: str
        """
        self.landsat8 = Landsat8()
        self.metadata_url = metadata_url

    def calibrate_landsat(self, image, band_list):
        """ Calibrate a stack of Landsat bands
        :type image: image.Image
        :type band_list: list[str]
        :rtype: numpy.ndarray
        """

        if image.band_count == 1:
            calibrated_image = self.calibrate_landsat_band(image.pixels, self.landsat8.band_number(band_list[0]))

        else:
            calibrated_image = np.zeros(image.shape)
            for i, band_name in enumerate(band_list):
                band_array = image.pixels[:, :, i]
                band_number = self.landsat8.band_number(band_name)

                calibrated_image[:, :, i] = self.calibrate_landsat_band(band_array, band_number)

        return Image(calibrated_image, image.geotransform, image.projection, image.metadata,
                     band_labels={i+1: band for i, band in enumerate(band_list)})

    def calibrate_landsat_band(self, band_array, band_number):
        """ Calibrate a single Landsat band
        :type band_array: numpy.ndarray
        :type band_number: int
        :rtype: numpy.ndarray
        """
        gain = self.get_landsat_metadata_value('REFLECTANCE_MULT_BAND_{}'.format(band_number))
        bias = self.get_landsat_metadata_value('REFLECTANCE_ADD_BAND_{}'.format(band_number))
        sun_elevation_degrees = self.get_landsat_metadata_value('SUN_ELEVATION')
        sun_elevation_radians = math.radians(sun_elevation_degrees)

        return self.calculate_landsat_toa_reflectance(band_array, gain, bias, sun_elevation_radians)

    def get_landsat_metadata_value(self, parameter):
        """ Extract value from metadata txt file
        :type parameter: str
        :rtype: float
        """
        metadata_file = urlopen(self.metadata_url)
        # TODO: Make this less ugly!
        for line in metadata_file:
            data = str(line).split(' = ')
            if(data[0]).split("'")[1].strip() == parameter:
                return float(data[1].split('\\')[0])

    @staticmethod
    def calculate_landsat_toa_reflectance(dn, gain, bias, sun_elevation):
        """ Calculate Top of Atmosphere reflectance taking into account solar geometry
        :type dn: numpy.ndarray
        :type gain: float
        :type bias: float
        :type sun_elevation: float
        :rtype: numpy.ndarray
        """
        rho = np.where(dn > 0, (gain*dn + bias) / math.sin(sun_elevation), 0)

        return rho
