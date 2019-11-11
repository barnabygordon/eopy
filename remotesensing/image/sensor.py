from abc import ABCMeta, abstractmethod
from typing import Dict


class Sensor(metaclass=ABCMeta):
    """ Abstract class describing what a sensor should look like """
    @abstractmethod
    def bands(self) -> Dict[str, int]:
        """ What bands are available for the sensor"""
        pass

    @abstractmethod
    def band_resolution(self, band_name: str) -> float:
        """ The resolution in metres for a spectral band"""
        pass


class Landsat8(Sensor):
    """ Landsat8 bands and band resolutions """
    @property
    def bands(self) -> Dict[str, int]:
        return {'coastal': 1, 'blue': 2, 'green': 3, 'red': 4, 'nir': 5, 'swir_1': 6,
                'swir_2': 7, 'pan': 8, 'cirrus': 9, 'tirs_1': 10, 'tirs_2': 11, 'BQA': 12}

    @classmethod
    def band_resolution(cls, band_name: str) -> Dict[str, int]:
        resolutions = {
            'coastal': 30., 'blue': 30., 'green': 30., 'red': 30., 'nir': 30., 'swir_1': 30.,
            'swir_2': 30., 'pan': 15., 'cirrus': 30., 'tirs_1': 30., 'tirs_2': 30., 'BQA': None}
        return resolutions[band_name]


class Sentinel2(Sensor):
    """ Sentinel2 bands and band resolutions """
    @property
    def bands(self) -> Dict[str, int]:
        return {'coastal': 0, 'blue': 1, 'green': 2, 'red': 3, 'red_edge_1': 4, 'red_edge_2': 5, 'red_edge_3': 6,
                'nir_1': 7, 'nir_2': 8, 'water_vapour': 9, 'swir_1': 10, 'swir_2': 11, 'swir_3': 12}

    def band_resolution(self, band_name: str) -> float:
        resolutions = {
            'coastal': 60., 'blue': 10., 'green': 10., 'red': 10., 'red_edge_1': 20.,
            'red_edge_2': 20., 'red_edge_3': 20., 'nir_1': 10., 'nir_2': 20., 'water_vapour': 60.,
            'swir_1': 60., 'swir_2': 20., 'swir_3': 20.}
        return resolutions[band_name]
