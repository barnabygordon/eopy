import requests
import geojson
from shapely.geometry import shape

from remotesensing.cloud.scene import Scene


class Searcher:
    """ A class to search for satellite imagery """
    def __init__(self):
        self._api_url = "api.developmentseed.org/satellites/"

    def search(self, start_date=None, end_date=None, boundary=None, longitude_latitude=None, path=None, row=None,
               cloud_min=0, cloud_max=100, search_limit=1000):
        """
        :type start_date: str
        :type end_date: str
        :type boundary: shapely.geometry.Polygon
        :type longitude_latitude: typing.Tuple(float)
        :type path: int
        :type row: int
        :type cloud_min: float
        :type cloud_max: float
        :type search_limit: int
        :rtype: typing.List[cloud.scene.Scene]
        """

        url = self._build_url(start_date, end_date, boundary, longitude_latitude, path, row, cloud_min, cloud_max,
                              search_limit)

        response = requests.get(url).json()

        if len(response['results']) == 0:
            raise NoSearchResultsFound

        scene_list = []
        for result in response['results']:
            polygon = shape(result['data_geometry'])
            area_coverage = self._calculate_area_coverage(boundary, polygon)

            scene_list.append(
                Scene(
                    identity=result['scene_id'],
                    satellite_name=result['satellite_name'],
                    cloud_coverage=result['cloud_coverage'],
                    area_coverage=area_coverage,
                    date=result['date'],
                    thumbnail=result['thumbnail'],
                    links=result['download_links']['aws_s3'],
                    polygon=polygon)
            )

        return scene_list

    def _build_url(self, start_date, end_date, boundary, longitude_latitude, path, row, cloud_min, cloud_max,
                   search_limit):

        url = "https://{root}?cloud_from={cloud_from}&cloud_to={cloud_to}&limit={limit}".format(
            root=self._api_url,
            cloud_from=cloud_min,
            cloud_to=cloud_max,
            limit=search_limit)

        if start_date:
            url += "&date_from={}".format(start_date)
        if end_date:
            url += "&date_to={}".format(end_date)
        if boundary:
            url += "&intersects={}".format(str(geojson.Feature(geometry=boundary)))
        if longitude_latitude:
            url += "&contains={longitude},{latitude}".format(
                longitude=longitude_latitude[0],
                latitude=longitude_latitude[1])
        if path:
            url += "&path={}".format(path)
        if row:
            url += "&row={}".format(row)

        return url

    def _calculate_area_coverage(self, search_boundary, scene_boundary):
        """
        :type search_boundary: shapely.geometry.Polygon
        :type scene_boundary: shapely.geometry.Polygon
        :rtype: float
        """

        intersection_area = scene_boundary.intersection(search_boundary).area

        if intersection_area != 0.:
            return (search_boundary.area / intersection_area) * 100
        else:
            return 0.


class NoSearchResultsFound(Exception):
    pass
