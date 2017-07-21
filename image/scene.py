from shapely.geometry import Polygon


class LandsatScene:
    """ Landsat-8 scene metadata """
    def __init__(self,
                 product_id: str,
                 date: str,
                 clouds: float,
                 bounds: Polygon,
                 download_links: [str],
                 thumbnail_url: str):
        self.produced_id = product_id
        self.path = self.string[3:6]
        self.row = self.string[6:9]
        self.date = date
        self.bounds = bounds
        self.clouds = int(clouds)
        self.download_links = download_links
        self.thumbnail_url = thumbnail_url

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
