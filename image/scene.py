from shapely.geometry import Polygon


class LandsatScene:
    """ Landsat-8 scene metadata """
    def __init__(self,
                 product_id: str,
                 date: str,
                 clouds: float,
                 path: str,
                 row: str,
                 bounds: Polygon,
                 thumbnail_url: str):
        self.product_id = product_id
        self.path = self._parse_path_row(path)
        self.row = self._parse_path_row(row)
        self.date = date
        self.bounds = bounds
        self.clouds = int(clouds)
        self.thumbnail_url = thumbnail_url
        self.download_path = "{url_root}/{collection}/{sensor}/{path}/{row}/{product_id}/{product_id}".format(
            url_root="https://landsat-pds.s3.amazonaws.com",
            collection='c1',
            sensor='L8',
            path=self.path,
            row=self.row,
            product_id=self.product_id)

    @staticmethod
    def _parse_path_row(string):
        if len(string) == 2:
            return '0{}'.format(string)
        else:
            return string

    def __repr__(self):
        return "Landsat-8 Scene | Clouds: {} | Date: {}".format(self.clouds, self.date)


class SentinelScene:
    """ Sentinel-2 scene metadata """
    def __init__(self, scene_id: str, date: str, clouds: float, bounds: Polygon, image_url: str):
        self.scene_id = scene_id
        self.date = date
        self.clouds = clouds
        self.bounds = bounds
        self.image_url = image_url

    def __repr__(self):
        return "Sentinel-2 Scene | Clouds: {} | Date: {}".format(self.clouds, self.date)
