from urllib.request import urlopen
import numpy as np
import math

from image import Landsat8


class Calibration:
    def __init__(self, metadata_url: str):
        self.landsat8 = Landsat8()
        self.metadata_file = urlopen(metadata_url)

    def calibrate_landsat(self, image: np.ndarray, band_list: [str]):
        calibrated_image = np.zeros(image.shape)
        for i, band_name in enumerate(band_list):
            band_array = image[:, :, i]
            band_number = self.landsat8.band_number(band_name)

            calibrated_image[:, :, i] = self.calibrate_landsat_band(band_array, band_number)

        return calibrated_image

    def calibrate_landsat_band(self, band_array, band_number):
        gain = self.get_landsat_metadata_value(self.metadata_file, 'REFLECTANCE_MULT_BAND_{}'.format(band_number))
        bias = self.get_landsat_metadata_value(self.metadata_file, 'REFLECTANCE_ADD_BAND_{}'.format(band_number))
        sun_elevation_degrees = self.get_landsat_metadata_value(self.metadata_file, 'SUN_ELEVATION')
        sun_elevation_radians = math.radians(sun_elevation_degrees)

        return self.calculate_landsat_toa_reflectance(band_array, gain, bias, sun_elevation_radians)

    def get_landsat_metadata_value(self, metadata_file, parameter):
        """ Extract value from metadata txt file
        :param metadata_file: Iterable from urllib.request.urlopen
        :param parameter: The desired parameter
        :return: value
        """
        for line in metadata_file:
            data = line.split(' = ')
            if(data[0]).strip() == parameter:
                return (data[1]).strip()

    def calculate_landsat_toa_reflectance(self, dn: np.ndarray, gain: float, bias: float, sun_elevation: float):
        """ Calculate Top of Atmosphere reflectance taking into account solar geometry
        :param dn: Digital Number
        :param gain: The band specific multiplicative rescaling factor
        :param bias: The band specific addititive rescaling factor
        :param sun_elevation: The angle of the sun in radians
        :return: Radiometrically corrected Landsat image
        """

        rho_prime = gain * dn + bias
        rho = rho_prime / np.sin(sun_elevation)

        return rho
