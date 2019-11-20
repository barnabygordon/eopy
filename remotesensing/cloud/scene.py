from IPython.display import Image as IPythonImage
from shapely.geometry import Polygon
from typing import List, Dict


class Scene:
    def __init__(self,
                 identity: str,
                 satellite_name: str,
                 cloud_coverage: float,
                 area_coverage: float,
                 date: str,
                 thumbnail: str,
                 polygon: Polygon,
                 links: Dict[str, Dict]):

        self.identity = identity
        self.satellite_name = satellite_name
        self.cloud_coverage = cloud_coverage
        self.area_coverage = area_coverage
        self.date = date
        self._thumbnail = thumbnail
        self.polygon = polygon
        self.links = links

    def __repr__(self):
        return f"<Scene: {self.identity}>"

    @property
    def show(self):
        return IPythonImage(self._thumbnail)

    @property
    def bands(self) -> List[str]:

        return list(self.links.keys())
