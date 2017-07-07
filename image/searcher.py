import requests
import time
import numpy as np
from shapely.geometry import Polygon
from xml.etree import ElementTree

import config


class Searcher:
    def __init__(self, cloud_min: int=0, cloud_max: int=100, search_limit: int=100):
        self.cloud_min = cloud_min
        self.cloud_max = cloud_max
        self.search_limit = search_limit
        self.username = config.username
        self.password = config.password

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
                bounds = np.squeeze(np.array(result['data_geometry']['coordinates']))
                polygon = Polygon(zip(bounds[:, 0], bounds[:, 1]))
                search_results.append(LandsatScene(
                    scene_id=result['scene_id'],
                    date=result['acquisitionDate'],
                    clouds=result['cloudCoverFull'],
                    bounds=polygon))

            return search_results

    def search_sentinel2_scenes(self, polygon: Polygon, start_date) -> dict:
        url = self._construct_sentinel2_search_url(polygon, start_date)

        response = requests.get(
            url,
            auth=(
                self.username,
                self.password)).json()

        feed = response['feed']
        results_count = feed['opensearch:totalResults']

        print('Found {} results'.format(results_count))

        search_results = []
        for r in feed['entry']:
            xml_response = self._get_sentinel2_metadata(r['id'])

            response = self._parse_xml(xml_response)
            name = response[-1][1].text
            date = response[2].text.split('T')[0]
            geometry = response[-1][11].text

            # TODO: calculate geopatial codes
            image_url = self._construct_sentinel2_image_url(
                name,
                utm_code,
                latitude_band,
                square)
            cloud_percentage = self._get_sentinel2_cloudcover(image_url)

            search_results.append({
                'date': date,
                'clouds': cloud_percentage,
                'scene_id': name,
                'image_url': image_url,
                'bounds': geometry})

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

    def _get_sentinel2_metadata(self, image_id):
        url_root = "https://scihub.copernicus.eu/dhus/odata/v1/Products"
        url = "{}('{}')".format(url_root, image_id)

        return requests.get(url, auth=(self.username, self.password))

    def _get_sentinel2_cloudcover(self, url):
        folder_path = url.split('tiles/')[1]
        metadata_url = 'http://sentinel-s2-l1c.s3.amazonaws.com/tiles/{}/metadata.xml'.format(folder_path)

        results = requests.get(metadata_url)
        tree = self._parse_xml(results.text)

        return tree[2][0][0].text

    @staticmethod
    def _construct_sentinel2_search_url(polygon: Polygon, start_date):
        url_root = 'https://scihub.copernicus.eu/dhus/search?q='

        area = 'footprint:"Intersects({})"'.format(polygon)
        #  TODO: Convert start date to days past
        time = 'ingestiondate:[NOW-{}DAYS TO NOW]'.format(start_date)
        product_type = 'S2MSI1C'
        rows = 100

        url = '{url_root}producttype:{product_type} AND {area} AND {time}&format=json&rows={rows}'.format(
            url_root=url_root, product_type=product_type, area=area, time=time, rows=rows)

        return url

    @staticmethod
    def _construct_sentinel2_image_url(scene_id, utm_zone, latitude_band, grid_square):
        url_root = 's3://sentinel-s2-l1c/tiles'
        sequence = '0'

        folder_url = '{url_root}/{utm_zone}/{latitude_band}/{grid_square}/{year}/{month}/{day}/{sequence}'.format(
            url_root=url_root, utm_zone=utm_zone, latitude_band=latitude_band, grid_square=grid_square,
            year=scene_id.year, month=scene_id.month, day=scene_id.day, sequence=sequence)

        return folder_url

    @staticmethod
    def _parse_xml(xml):
        return ElementTree.fromstring(xml)


class LandsatScene:
    def __init__(self, scene_id: str, date: str, clouds: int, bounds: Polygon):
        self.string = scene_id
        self.path = int(self.string[3:6])
        self.row = int(self.string[6:9])
        self.year = int(self.string[9:13])
        self.month = int(self.string[13:14])
        self.day = int(self.string[14:16])
        self.bounds = bounds
        self.clouds = int(clouds)
        self.date = date
