from abc import ABCMeta
from abc import abstractproperty


class Sensor(metaclass=ABCMeta):

    @abstractproperty
    def available_bands(self) -> list:
        pass

    @abstractproperty
    def band_number(self, band_name: str) -> int:
        pass

    @abstractproperty
    def band_resolution(self, band_name: str) -> float:
        pass


class Landsat8(Sensor):
    @property
    def available_bands(self) -> list:
        return ['coastal', 'blue', 'green', 'red', 'nir', 'swir_1',
                'swir_2', 'pan', 'cirrus', 'tirs_1', 'tirs_2', 'BQA']

    @property
    def band_number(self, band_name: str) -> int:
        return self.available_bands.index(band_name) + 1

    @property
    def band_resolution(self, band_name: str) -> float:
        resolutions = {
            'coastal': 30., 'blue': 30., 'green': 30., 'red': 30., 'nir': 30., 'swir_1': 30.,
            'swir_2': 30., 'pan': 15., 'cirrus': 30., 'tirs_1': 30., 'tirs_2': 30., 'BQA': None}
        return resolutions[band_name]


class Sentinel2(Sensor):
    @property
    def available_bands(self):
        return None

    @property
    def band_number(self, band_name: str):
        return None

    @property
    def band_resolution(self, band_name: str):
        return None
