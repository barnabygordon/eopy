from urllib.request import urlopen
import numpy as np
import math

from image import Landsat8


class Calibration:
    """ Functionality to calibrate satellite data """
    def __init__(self, metadata_url: str):
        self.landsat8 = Landsat8()
        self.metadata_url = metadata_url

    def calibrate_landsat(self, image: np.ndarray, band_list: [str]) -> np.ndarray:
        """ Calibrate a stack of Landsat bands
        :param image: Stack of Landsat bands with shape (columns, rows, bands)
        :param band_list: List of band names
        :return: Stack of calibrated Landsat bands
        """

        if image.ndim == 2:
            calibrated_image = self.calibrate_landsat_band(image, self.landsat8.band_number(band_list[0]))

        else:
            calibrated_image = np.zeros(image.shape)
            for i, band_name in enumerate(band_list):
                band_array = image[:, :, i]
                band_number = self.landsat8.band_number(band_name)

                calibrated_image[:, :, i] = self.calibrate_landsat_band(band_array, band_number)

        return calibrated_image

    def calibrate_landsat_band(self, band_array: np.ndarray, band_number: int) -> np.ndarray:
        """ Calibrate a single Landsat band
        :param band_array: 2D numpy array
        :param band_number: Number of the band
        :return: 2D calibrated numpy array
        """
        gain = self.get_landsat_metadata_value('REFLECTANCE_MULT_BAND_{}'.format(band_number))
        bias = self.get_landsat_metadata_value('REFLECTANCE_ADD_BAND_{}'.format(band_number))
        sun_elevation_degrees = self.get_landsat_metadata_value('SUN_ELEVATION')
        sun_elevation_radians = math.radians(sun_elevation_degrees)

        return self.calculate_landsat_toa_reflectance(band_array, gain, bias, sun_elevation_radians)

    def get_landsat_metadata_value(self, parameter):
        """ Extract value from metadata txt file
        :param parameter: The desired parameter
        :return: value
        """
        metadata_file = urlopen(self.metadata_url)
        for line in metadata_file:
            data = str(line).split(' = ')
            print(data[0].split("'")[1].strip(), parameter)
            if(data[0]).split("'")[1].strip() == parameter:
                return float(data[1].split('\\')[0])

    @staticmethod
    def calculate_landsat_toa_reflectance(dn: np.ndarray, gain: float, bias: float, sun_elevation: float):
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
