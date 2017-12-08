import requests
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
        :type boundary: str
        :type longitude_latitude: typing.Tuple(float)
        :type path: int
        :type row: int
        :type cloud_min: float
        :type cloud_max: float
        :type search_limit: int
        :rtype: typing.List[cloud.scene.Scene]
        """

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
            url += "&intersects={}".format(boundary)
        if longitude_latitude:
            url += "&contains={longitude},{latitude}".format(
                longitude=longitude_latitude[0],
                latitude=longitude_latitude[1])
        if path:
            url += "&path={}".format(path)
        if row:
            url += "&row={}".format(row)

        response = requests.get(url).json()

        scene_list = []
        for result in response['results']:
            scene_list.append(
                Scene(
                    identity=result['scene_id'],
                    satellite_name=result['satellite_name'],
                    cloud_coverage=result['cloud_coverage'],
                    date=result['date'],
                    thumbnail=result['thumbnail'],
                    links=result['download_links']['aws_s3'],
                    polygon=shape(result['data_geometry'])
                )
            )

        return scene_list
