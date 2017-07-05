import requests
import time
from shapely.geometry import Polygon


class Searcher:
    def __init__(self, cloud_min: int=0, cloud_max: int=100, search_limit: int=100):
        self.cloud_min = cloud_min
        self.cloud_max = cloud_max
        self.search_limit = search_limit

    def search_landsat8_scenes(self, polygon: Polygon, start_date) -> dict:
        url = self._construct_landsat8_search_url(polygon, start_date)

        response = requests.get(url).json()

        try:
            print(response['error']['message'])
        except:
            results_count = len(response['results'])
            print('Found {} results'.format(results_count))

            search_results = []
            for i, result in enumerate(response['results']):
                search_results.append({
                    'date': result['acquisitionDate'],
                    'clouds': result['cloudCoverFull'],
                    'scene_id': LandsatSceneID(result['scene_id']),
                    'bounds': result['data_geometry']['coordinates']})

            return search_results

    def _construct_landsat8_search_url(self, polygon: Polygon, start_date):
        url_root = 'https://api.developmentseed.org/satellites/landsat'

        search_bounds = polygon.bounds

        upper_left_latitude = search_bounds[3]
        lower_right_latitude = search_bounds[1]
        lower_left_longitude = search_bounds[0]
        upper_right_longitude = search_bounds[2]

        today = time.strftime("%Y-%m-%d")

        date_string = 'acquisitionDate:[{}+TO+{}]'.format(start_date, today)
        cloud_string = 'cloudCoverFull:[{}+TO+{}]'.format(self.cloud_min, self.cloud_max)
        left_latitude_string = 'upperLeftCornerLatitude:[{}+TO+1000]'.format(upper_left_latitude)
        right_latitude_string = 'lowerRightCornerLatitude:[-1000+TO+{}]'.format(lower_right_latitude)
        left_longitude_string = 'lowerLeftCornerLongitude:[-1000+TO+{}]'.format(lower_left_longitude)
        right_longitude_string = 'upperRightCornerLongitude:[{}+TO+1000]'.format(upper_right_longitude)
        limit_string = 'limit={}'.format(self.search_limit)

        search_string = '{}+AND+{}+AND+{}+AND+{}+AND+{}+AND+{}&{}'.format(
            date_string, cloud_string,
            left_latitude_string, right_latitude_string,
            left_longitude_string, right_longitude_string,
            limit_string)

        url = '{}?search={}'.format(url_root, search_string)

        return url


class LandsatSceneID:
    def __init__(self, scene_id_string: str):
        self.string = scene_id_string
        self.path = self.string[3:6]
        self.row = self.string[6:9]
        self.year = self.string[9:14]
        self.month = self.string[14:16]
        self.day = self.string[16:18]
