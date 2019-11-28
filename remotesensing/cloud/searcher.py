import requests
import json
from enum import Enum
from datetime import datetime
from typing import List
from shapely.geometry import shape, Polygon

from remotesensing.cloud.scene import Scene
from remotesensing.geometry import GeoPolygon
from remotesensing.tools import gis


class Satellite(Enum):

    Sentinel2 = 'sentinel-2-l1c'
    Landsat8 = 'landsat-8-l1'


class Searcher:

    def __init__(self):
        self._api_url = 'https://sat-api.developmentseed.org/stac/search'

    def search(
            self,
            boundary: GeoPolygon,
            satellite: Satellite = None,
            start: datetime = None, end: datetime = None,
            cloud_min: float = 0, cloud_max: float = 100,
            limit: int = 1000) -> List[Scene]:

        params = {
            'bbox': list(boundary.polygon.exterior.bounds),
            'limit': limit,
            'query': {
                'eo:cloud_cover': {
                    'lt': cloud_max,
                    'gt': cloud_min
                }
            },
            'sort': [
                {
                    'field': 'datetime',
                    'direction': 'desc'
                }
            ]
        }

        if satellite:
            params['query']['collection'] = {
                'eq': satellite.value
            }

        if start:
            time_query = f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}"
            if end:
                time_query += f"/{end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
            params['time'] = time_query

        response = requests.post(self._api_url, data=json.dumps(params), headers={'Content-Type': 'application/json'})
        response_json = response.json()

        if len(response_json['features']) == 0:
            raise NoSearchResultsFound()

        scene_list = []
        for result in response_json['features']:
            polygon = shape(result.get('geometry'))
            area_coverage = self._calculate_area_coverage(boundary.polygon, polygon)
            properties = result.get('properties', {})

            scene_list.append(
                Scene(
                    identity=result.get('id'),
                    satellite_name=properties.get('eo:platform'),
                    cloud_coverage=properties.get('eo:cloud_cover'),
                    area_coverage=area_coverage,
                    date=datetime.strptime(properties.get('datetime').split('.')[0], '%Y-%m-%dT%H:%M:%S'),
                    thumbnail=result.get('assets', {}).get('thumbnail', {}).get('href'),
                    links=result.get('assets', {}),
                    polygon=GeoPolygon(polygon, epsg=gis.WGS84_EPSG),
                    epsg=properties.get('eo:epsg')
                )
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
