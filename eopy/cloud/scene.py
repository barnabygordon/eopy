from IPython.display import Image as IPythonImage
from typing import List, Dict
from datetime import datetime

from eopy.geometry import GeoPolygon


class Scene:
    def __init__(self,
                 identity: str,
                 satellite_name: str,
                 cloud_coverage: float,
                 area_coverage: float,
                 date: datetime,
                 thumbnail: str,
                 polygon: GeoPolygon,
                 links: Dict[str, Dict],
                 epsg: int):

        self.identity = identity
        self.satellite_name = satellite_name
        self.cloud_coverage = cloud_coverage
        self.area_coverage = area_coverage
        self.date = date
        self._thumbnail = thumbnail
        self.polygon = polygon
        self.links = links
        self.epsg = epsg

    def __repr__(self):
        return f"<Scene: {self.identity} | Cloud: {self.cloud_coverage} | Date: {self.date.strftime('%Y-%m-%d')}>"

    @property
    def show(self):
        return IPythonImage(self._thumbnail)

    @property
    def bands(self) -> List[str]:

        return list(self.links.keys())
