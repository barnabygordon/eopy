from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty

LANDSAT_8_LOOKUP = {
    'coastal': 1, 'blue': 2, 'green': 3, 'red': 4,
    'nir': 5, 'swir_1': 6, 'swir_2': 7, 'pan': 8,
    'cirrus': 9, 'tirs_1': 10, 'tirs_2': 11, 'BQA': 12}


class Sensor(metaclass=ABCMeta):

    @abstractproperty
    def available_bands(self) -> dict:
        pass

    @abstractproperty
    def band_number(self, band_name: str) -> int:
        pass

    @abstractproperty
    def band_resolution(self, band_name: str) -> float:
        pass


class Landsat8(Sensor):
    @property
    def available_bands(self):
        return None

    @property
    def band_number(self, band_name: str):
        return None

    @property
    def band_resolution(self, band_name: str):
        return None


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
