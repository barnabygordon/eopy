from abc import ABCMeta
from abc import abstractproperty
from abc import abstractclassmethod


class Sensor(metaclass=ABCMeta):

    @abstractproperty
    def available_bands(self) -> list:
        pass

    @abstractclassmethod
    def band_number(self, band_name: str) -> int:
        pass

    @abstractclassmethod
    def band_resolution(self, band_name: str) -> float:
        pass


class Landsat8(Sensor):
    @property
    def available_bands(self) -> list:
        return ['coastal', 'blue', 'green', 'red', 'nir', 'swir_1',
                'swir_2', 'pan', 'cirrus', 'tirs_1', 'tirs_2', 'BQA']

    @classmethod
    def band_number(self, band_name: str) -> int:
        return self.available_bands.index(band_name) + 1

    @classmethod
    def band_resolution(self, band_name: str) -> float:
        resolutions = {
            'coastal': 30., 'blue': 30., 'green': 30., 'red': 30., 'nir': 30., 'swir_1': 30.,
            'swir_2': 30., 'pan': 15., 'cirrus': 30., 'tirs_1': 30., 'tirs_2': 30., 'BQA': None}
        return resolutions[band_name]


class Sentinel2(Sensor):
    @property
    def available_bands(self) -> list:
        return ['coastal', 'blue', 'green', 'red', 'red_edge_1', 'red_edge_2', 'red_edge_3',
                'nir_1', 'nir_2', 'water_vapour', 'swir_1', 'swir_2', 'swir_3']

    @classmethod
    def band_number(self, band_name: str) -> int:
        return self.available_bands.index(band_name) + 1

    @classmethod
    def band_resolution(self, band_name: str) -> float:
        resolutions = {
            'coastal': 60., 'blue': 10., 'green': 10., 'red': 10., 'red_edge_1': 20.,
            'red_edge_2': 20., 'red_edge_3': 20., 'nir_1': 10., 'nir_2': 20., 'water_vapour': 60.,
            'swir_1': 60., 'swir_2': 20., 'swir_3': 20.}
        return resolutions[band_name]
