from shapely.geometry import Polygon
from IPython.display import Image as IPythonImage


class SatelliteScene:
    def __init__(self, satllite_type: str, date: str, clouds: float, bounds: Polygon):
        self.satellite_type = satllite_type
        self.date = date
        self.clouds = clouds
        self.bounds = bounds

    def __repr__(self):
        return "{} Scene | Clouds: {} | Date: {}".format(self.satellite_type, self.clouds, self.date)


class LandsatScene(SatelliteScene):
    """ Landsat-8 scene metadata """
    def __init__(self,
                 product_id: str,
                 date: str,
                 clouds: float,
                 path: str,
                 row: str,
                 bounds: Polygon,
                 thumbnail_url: str):
        SatelliteScene.__init__(self, "Landsat-8", date, clouds, bounds)
        self.product_id = product_id
        self.path = self._parse_path_row(path)
        self.row = self._parse_path_row(row)
        self.thumbnail_url = thumbnail_url
        self.download_path = "{url_root}/{collection}/{sensor}/{path}/{row}/{product_id}/{product_id}".format(
            url_root="https://landsat-pds.s3.amazonaws.com",
            collection='c1',
            sensor='L8',
            path=self.path,
            row=self.row,
            product_id=self.product_id)

    @property
    def show(self):
        return IPythonImage(self.thumbnail_url)

    @staticmethod
    def _parse_path_row(string):
        if len(string) == 2:
            return '0{}'.format(string)
        else:
            return string


class SentinelScene(SatelliteScene):
    """ Sentinel-2 scene metadata """
    def __init__(self, scene_id: str, date: str, clouds: float, bounds: Polygon, image_url: str):
        SatelliteScene.__init__(self, "Sentinel-2", date, clouds, bounds)
        self.type = "Sentinel-2"
        self.scene_id = scene_id
        self.image_url = image_url
