import math
from typing import List, Dict
from urllib.request import urlopen

import numpy as np
from remotesensing.image import Image


class Calibrator:

    def calibrate_landsat(self, image: Image, metadata_url: str, band_list: List[int]) -> Image:

        metadata = self._get_metadata(metadata_url)

        if image.band_count == 1:
            calibrated_pixels = self._calibrate_landsat_band(image.pixels, metadata, band_list[0])
        else:
            calibrated_pixels = np.zeros(image.shape)
            for i, band in enumerate(band_list):
                band_pixels = image.pixels[:, :, i]
                calibrated_pixels[:, :, i] = self._calibrate_landsat_band(band_pixels, metadata, band)

        return Image(calibrated_pixels, image.geotransform, image.projection)

    def _calibrate_landsat_band(self, band: np.ndarray, metadata: Dict[str, str], band_number: int) -> np.ndarray:

        gain = float(metadata[f'REFLECTANCE_MULT_BAND_{band_number}'])
        bias = float(metadata[f'REFLECTANCE_ADD_BAND_{band_number}'])
        sun_elevation_degrees = float(metadata['SUN_ELEVATION'])

        sun_elevation_radians = math.radians(sun_elevation_degrees)

        return self._calculate_landsat_toa_reflectance(band, gain, bias, sun_elevation_radians)

    @staticmethod
    def _get_metadata(url: str) -> Dict[str, str]:

        metadata = {}
        for l in urlopen(url):

            try:
                key, value = str(l).strip("b'").strip(' ').strip('\\n').split(' = ')
                metadata[key] = value
            except ValueError:
                continue

        return metadata

    @staticmethod
    def _calculate_landsat_toa_reflectance(dn: np.ndarray, gain: float, bias: float, sun_elevation: float) -> np.ndarray:
        """ Calculate Top of Atmosphere reflectance taking into account solar geometry"""

        rho = np.where(dn > 0, (gain*dn + bias) / math.sin(sun_elevation), 0)

        return rho
