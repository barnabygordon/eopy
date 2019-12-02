import math
from typing import List, Dict
from urllib.request import urlopen

import numpy as np
from remotesensing.image import Image


class Calibrator:

    def calibrate_landsat(self, image: Image, metadata_url: str, band_list: List[int]) -> Image:

        metadata = self._get_metadata(metadata_url)

        if len(band_list) != image.band_count:
            raise UserWarning(f'{len(band_list)} bands provided but image has {image.band_count} bands')

        if image.band_count == 1:
            return self._calibrate_landsat_band(image, metadata, band_list[0])
        else:
            calibrated_bands = []
            for i, band_number in enumerate(band_list):
                calibrated_bands.append(self._calibrate_landsat_band(image[:, :, i], metadata, band_number))

            return image.stack(calibrated_bands)

    def _calibrate_landsat_band(self, band: Image, metadata: Dict[str, str], band_number: int) -> Image:

        gain = float(metadata[f'REFLECTANCE_MULT_BAND_{band_number}'])
        bias = float(metadata[f'REFLECTANCE_ADD_BAND_{band_number}'])
        sun_elevation_degrees = float(metadata['SUN_ELEVATION'])

        sun_elevation_radians = math.radians(sun_elevation_degrees)

        return band.apply(lambda x: self._calculate_landsat_toa_reflectance(x, gain, bias, sun_elevation_radians))

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
