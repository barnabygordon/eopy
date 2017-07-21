import requests
import json
import numpy as np
from shapely.geometry import Polygon
from xml.etree import ElementTree

from tools import gis
from tools.url_builder import URLBuilder
from image.scene import LandsatScene, SentinelScene
import config


class Searcher:
    """ A class to search for satellite imagery """
    def __init__(self, cloud_min: int=0, cloud_max: int=100, search_limit: int=100):
        """
        :param cloud_min: Minimum percentage of clouds per scene
        :param cloud_max: Maximum percentage of clouds per scene
        :param search_limit: Search limit
        """
        self.cloud_min = cloud_min
        self.cloud_max = cloud_max
        self.search_limit = search_limit
        self.username = config.username
        self.password = config.password

    def search_landsat8_scenes(self, aoi: Polygon, start_date: str) -> [LandsatScene]:
        """ Search for downloadable Landsat-8 scenes
        :param aoi: A WKT polygon defining the search AOI
        :param start_date: Start date from which to begin the search (YYYY-MM-DD)
        :return: A list of LandsatScenes
        """
        url = URLBuilder.build_landsat8_search_url(
            aoi,
            start_date,
            cloud_min=self.cloud_min, cloud_max=self.cloud_max,
            search_limit=self.search_limit)

        response = requests.get(url).json()

        try:
            print(response['error']['message'])
        except:
            results_count = len(response['results'])
            print('Found {} results'.format(results_count))

            search_results = []
            for i, result in enumerate(response['results']):
                bounds = np.squeeze(np.array(result['data_geometry']['coordinates']))
                polygon = Polygon(zip(bounds[:, 0], bounds[:, 1]))
                search_results.append(LandsatScene(
                    product_id=result['LANDSAT_PRODUCT_ID'],
                    date="".join(result['acquisitionDate'].split('-')),
                    clouds=result['cloudCoverFull'],
                    bounds=polygon,
                    download_links=result['download_links']['aws_s3'],
                    thumbnail_url=result['browseURL']))

            return search_results

    def search_sentinel2_scenes(self, aoi: Polygon, start_date) -> [SentinelScene]:
        """ Search for downloadable Sentinel-2 scenes within AOI and after date
        :param aoi: WKT polygon AOI
        :param start_date: date of start of search (YYYY-MM-DD)
        :return: list of SentinelScene objects
        """
        url = URLBuilder.build_sentinel2_search_url(aoi, start_date)
        utm_code, latitude_band, square = gis.get_mgrs_info(aoi)

        response = requests.get(
            url,
            auth=(
                self.username,
                self.password))

        assert response.status_code == 200, 'Search error: {}'.format(response.reason)

        content = json.loads(response.content.decode('utf-8'))

        feed = content['feed']
        results_count = feed['opensearch:totalResults']

        print('Found {} results'.format(results_count))

        search_results = []
        for r in feed['entry']:
            date = r['summary'].split(',')[0].split(' ')[1].split('T')[0]
            year, month, day = date.split('-')
            if type(r['double']) == list:
                for metric in r['double']:
                    if metric['name'] == 'cloudcoverpercentage':
                        cloud_percentage = metric['content']
            elif r['double']['name'] == 'cloudcoverpercentage':
                cloud_percentage = r['double']['content']
            else:
                print('Cloud Percentage not recorded')
                cloud_percentage = 999
            name = r['title']

            boundary_xml = ElementTree.fromstring(r['str'][1]['content'])

            for boundary in boundary_xml.findall('{http://www.opengis.net/gml}outerBoundaryIs'):
                for ring in boundary.findall('{http://www.opengis.net/gml}LinearRing'):
                    for coord in ring.findall('{http://www.opengis.net/gml}coordinates'):
                        coordinates = coord.text.split(' ')

            coords = np.array([(float(coord.split(',')[0]), float(coord.split(',')[1])) for coord in coordinates])
            boundary = Polygon(coords)

            image_url = URLBuilder.build_sentinel2_image_url(
                year, int(month), int(day),
                utm_code,
                latitude_band,
                square)

            search_results.append(
                SentinelScene(
                    scene_id=name,
                    date=date,
                    clouds=cloud_percentage,
                    bounds=boundary,
                    image_url=image_url))

        return search_results
