import json
import math

import numpy as np
import requests
from shapely import wkt
from shapely.geometry import Polygon
from tqdm import tqdm

from notebooks import config
from remotesensing.cloud.scene import LandsatScene, SentinelScene
from remotesensing.tools.url_builder import URLBuilder
from remotesensing.tools import gis


class Searcher:
    """ A class to search for satellite imagery """
    def __init__(self):
        self.username = config.username
        self.password = config.password
        self.url_builder = URLBuilder()

    def search_landsat8_scenes(self, start_date, aoi=None, path=None, row=None,
                               cloud_min=0, cloud_max=100, search_limit=300, verbose=True):
        """ Search for downloadable Landsat-8 scenes
        :type start_date: str
        :type aoi: shapely.geometry.Polygon
        :type path: int
        :type row: int
        :type cloud_min: int
        :type cloud_max: int
        :type search_limit: int
        :type verbose: bool
        :rtype: list[cloud.scene.LandsatScene]
        """
        url = self.url_builder.build_landsat8_search_url(
            start_date,
            polygon=aoi,
            path=path, row=row,
            cloud_min=cloud_min, cloud_max=cloud_max,
            search_limit=search_limit)

        response = requests.get(url).json()

        print(url)

        try:
            print(response['error']['message'])
        except:
            results_count = len(response['results'])
            if verbose:
                print('Found {} results'.format(results_count))

            search_results = []
            for i, result in enumerate(response['results']):
                bounds = np.squeeze(np.array(result['data_geometry']['coordinates']))
                polygon = Polygon(zip(bounds[:, 0], bounds[:, 1]))
                search_results.append(LandsatScene(
                    product_id=result['LANDSAT_PRODUCT_ID'],
                    date="".join(result['acquisitionDate'].split('-')),
                    path=str(result['path']),
                    row=str(result['row']),
                    clouds=result['cloudCoverFull'],
                    bounds=polygon,
                    thumbnail_url=result['browseURL']))

            return search_results

    def search_sentinel2_scenes(self, aoi, start_date):
        """
        :type aoi: shapely.geometry.Polygon
        :type start_date: str
        :rtype: list[cloud.scene.SentinelScene]
        """
        return self.search_sentinel_scenes(aoi, start_date, platform='Sentinel-2')

    def search_sentinel1_scenes(self, aoi, start_date):
        """
        :type aoi: shapely.geometry.Polygon
        :type start_date: str
        :rtype: list[cloud.scene.SentinelScene]
        """
        return self.search_sentinel_scenes(aoi, start_date, platform='Sentinel-1')

    def search_sentinel_scenes(self, aoi, start_date, platform):
        """ Search for downloadable Sentinel scenes within AOI and after date
        :type aoi: shapely.geometry.Polygon
        :type start_date: str
        :type platform: str
        :rtype: list[cloud.scene.SentinelScene]
        """

        url = URLBuilder.build_sentinel_search_url(aoi, start_date, platform, 0)
        response = requests.get(url, auth=(self.username, self.password))

        assert response.status_code == 200, 'Search error: {}'.format(response.reason)

        content = json.loads(response.content.decode('utf-8'))
        feed = content['feed']
        results_count = int(feed['opensearch:totalResults'])
        print('Found {} results'.format(results_count))

        search_results = []
        pagination_count = math.ceil(results_count / 100)
        for i in tqdm(range(pagination_count), total=pagination_count, desc='Paginating search results'):
            url = URLBuilder.build_sentinel_search_url(aoi, start_date, platform, i*100)
            response = requests.get(url, auth=(self.username, self.password))

            content = json.loads(response.content.decode('utf-8'))
            feed = content['feed']

            for r in feed['entry']:
                date = r['date'][0]['content'].split('T')[0]
                year, month, day = date.split('-')

                if platform == 'Sentinel-2':
                    if type(r['double']) == list:
                        for metric in r['double']:
                            if metric['name'] == 'cloudcoverpercentage':
                                cloud_percentage = metric['content']
                    elif r['double']['name'] == 'cloudcoverpercentage':
                        cloud_percentage = r['double']['content']
                else:
                    cloud_percentage = 999
                name = r['title']

                boundary = wkt.loads([i for i in r['str'] if 'POLYGON' in i['content']][0]['content'])

                utm_code, latitude_band, square = gis.get_mgrs_info(aoi)
                image_url = URLBuilder.build_sentinel2_image_url(
                    year, int(month), int(day),
                    utm_code, latitude_band, square)

                search_results.append(
                    SentinelScene(
                        scene_id=name,
                        date=date,
                        clouds=cloud_percentage,
                        bounds=boundary,
                        image_url=image_url))

        return search_results
