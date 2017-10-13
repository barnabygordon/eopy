from IPython.display import Image as IPythonImage


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
        self.date = date
        self.clouds = clouds
        self.bounds = bounds

    def __repr__(self):
        return "{} Scene | Clouds: {} | Date: {}".format(self.satellite_type, self.clouds, self.date)


class LandsatScene(SatelliteScene):
    """ Landsat-8 scene metadata """
    def __init__(self, product_id, date, clouds, path, row, bounds, thumbnail_url):
        """
        :type product_id: str
        :type date: str
        :type clouds: float
        :type path: str
        :type row: str
        :type bounds: shapely.geometry.Polygon
        :type thumbnail_url: str
        """
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
