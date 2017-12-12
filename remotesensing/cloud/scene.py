from IPython.display import Image as IPythonImage


class Scene:
    def __init__(self, identity, satellite_name, cloud_coverage, area_coverage, date, thumbnail, polygon, links):
        """
        :type identity: str
        :type satellite_name: str
        :type cloud_coverage: float
        :type area_coverage: float
        :type date: str
        :type thumbnail: str
        :type polygon: shapely.geometry.Polygon
        :type links: typing.List[str]
        """

        self._identity = identity
        self._satellite_name = satellite_name
        self._cloud_coverage = cloud_coverage
        self._area_coverage = area_coverage
        self._date = date
        self._thumbnail = thumbnail
        self._polygon = polygon
        self._links = links

    @property
    def identity(self):
        return self._identity

    @property
    def satellite_name(self):
        return self._satellite_name

    @property
    def links(self):
        return self._links

    @property
    def cloud_coverage(self):
        return self._cloud_coverage

    @property
    def area_coverage(self):
        return self._area_coverage

    @property
    def polygon(self):
        return self._polygon

    @property
    def date(self):
        return self._date

    def __repr__(self):
        return "<Scene: {}>".format(self._identity)

    @property
    def show(self):
        return IPythonImage(self._thumbnail)

