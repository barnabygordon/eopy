import requests
from datetime import datetime
from typing import List
from shapely.geometry import shape, Polygon

from remotesensing.cloud.scene import Scene


class Searcher:
    """ A class to search for satellite imagery """
    def __init__(self):
        self._api_url = 'https://sat-api.developmentseed.org/stac/search'

    def search(
            self,
            boundary: Polygon,
            start: datetime = None, end: datetime = None,
            cloud_min: float = 0, cloud_max: float = 100,
            limit: int = 1000) -> List[Scene]:

        params = {
            'bbox': list(boundary.exterior.bounds),
            'query': {
                'eo:cloud_cover': {
                    'lt': cloud_min,
                    'gt': cloud_max
                }
            },
            'limit': limit,
            'sort': [
                {
                    'field': 'time',
                    'direction': 'desc'
                }
            ]
        }

        if start:
            time_query = f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}"
            if end:
                time_query += f"/{end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
            params['time'] = time_query

        response = requests.post(self._api_url, params=params, headers={'Accept': 'application/geo+json'})
        response_json = response.json()

        if len(response_json['features']) == 0:
            raise NoSearchResultsFound()

        scene_list = []
        for result in response_json['features']:
            polygon = shape(result.get('geometry'))
            area_coverage = self._calculate_area_coverage(boundary, polygon)

            scene_list.append(
                Scene(
                    identity=result.get('id'),
                    satellite_name=result.get('properties', {}).get('eo:platform'),
                    cloud_coverage=result.get('properties', {}).get('eo:cloud_cover'),
                    area_coverage=area_coverage,
                    date=datetime.strptime(result.get('properties', {}).get('datetime').split('.')[0], '%Y-%m-%dT%H:%M:%S'),
                    thumbnail=result.get('assets', {}).get('thumbnail', {}).get('href'),
                    links=result.get('assets', {}),
                    polygon=polygon)
            )

        return scene_list

    @staticmethod
    def _calculate_area_coverage(search_boundary: Polygon, scene_boundary: Polygon) -> float:

        intersection_area = scene_boundary.intersection(search_boundary).area

        if intersection_area != 0.:
            return (search_boundary.area / intersection_area) * 100
        else:
            return 0.


class NoSearchResultsFound(Exception):
    pass
