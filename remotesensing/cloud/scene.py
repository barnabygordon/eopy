from IPython.display import Image as IPythonImage
from datetime import datetime


class SatelliteScene:
    """ A generic satellite scene """
    def __init__(self, satellite_type, date, clouds, bounds):
        """
        :type satellite_type: str
        :type date: str
        :type clouds: float
        :type bounds: shapely.geometry.Polygon
        """
        self.satellite_type = satellite_type
        self.date = datetime.strptime(date, "%Y%m%d")
        self.clouds = clouds
        self.bounds = bounds

    def __repr__(self):
        return "{} Scene | Clouds: {} | Date: {}".format(self.satellite_type, self.clouds, self.date)


class LandsatScene(SatelliteScene):
    """ Landsat-8 scene metadata """
    def __init__(self, product_id, scene_id, date, clouds, path, row, bounds, thumbnail_url):
        """
        :type product_id: str
        :type scene_id: str
        :type date: str
        :type clouds: float
        :type path: str
        :type row: str
        :type bounds: shapely.geometry.Polygon
        :type thumbnail_url: str
        """
        SatelliteScene.__init__(self, "Landsat-8", date, clouds, bounds)
        self.product_id = product_id
        self.scene_id = scene_id
        self.path = self._parse_path_row(path)
        self.row = self._parse_path_row(row)
        self.thumbnail_url = thumbnail_url
        self.pre_collection_date = datetime.strptime("20170501", "%Y%m%d")
        self.url_root = "https://landsat-pds.s3.amazonaws.com"
        self.download_path = self._construct_download_link()

    @property
    def show(self):
        return IPythonImage(self.thumbnail_url)

    def _construct_download_link(self):
        if self.date < self.pre_collection_date:
            return '{url_root}/L8/{path}/{row}/{scene_id}/{scene_id}'.format(
                url_root=self.url_root,
                path=self.path,
                row=self.row,
                scene_id=self.scene_id.split('LGN')[0] + 'LGN00')
        else:
            return '{url_root}/c1/L8/{path}/{row}/{product_id}/{product_id}'.format(
                url_root=self.url_root,
                path=self.path,
                row=self.row,
                product_id=self.product_id)

    @staticmethod
    def _parse_path_row(string):
        if len(string) == 2:
            return '0{}'.format(string)
        else:
            return string


class SentinelScene(SatelliteScene):
    """ Sentinel scene metadata """
    def __init__(self, scene_id, date, clouds, bounds, image_url):
        """
        :type scene_id: str
        :type date: str
        :type clouds: float
        :type bounds: shapely.geometry.Polygon
        :type image_url: str
        """
        SatelliteScene.__init__(self, "Sentinel", date, clouds, bounds)
        self.scene_id = scene_id
        self.image_url = image_url
