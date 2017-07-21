from shapely.geometry import Polygon
import time


class URLBuilder:
    @staticmethod
    def build_landsat8_search_url(polygon: Polygon, start_date, cloud_min, cloud_max, search_limit):
        """ Defines a Landsat-8 search url for development seed """
        url_root = 'https://api.developmentseed.org/satellites/landsat'

        search_bounds = polygon.bounds

        upper_left_latitude = search_bounds[3]
        lower_right_latitude = search_bounds[1]
        lower_left_longitude = search_bounds[0]
        upper_right_longitude = search_bounds[2]

        today = time.strftime("%Y-%m-%d")

        date_string = 'acquisitionDate:[{}+TO+{}]'.format(start_date, today)
        cloud_string = 'cloudCoverFull:[{}+TO+{}]'.format(cloud_min, cloud_max)
        left_latitude_string = 'upperLeftCornerLatitude:[{}+TO+1000]'.format(upper_left_latitude)
        right_latitude_string = 'lowerRightCornerLatitude:[-1000+TO+{}]'.format(lower_right_latitude)
        left_longitude_string = 'lowerLeftCornerLongitude:[-1000+TO+{}]'.format(lower_left_longitude)
        right_longitude_string = 'upperRightCornerLongitude:[{}+TO+1000]'.format(upper_right_longitude)
        limit_string = 'limit={}'.format(search_limit)

        search_string = '{}+AND+{}+AND+{}+AND+{}+AND+{}+AND+{}&{}'.format(
            date_string, cloud_string,
            left_latitude_string, right_latitude_string,
            left_longitude_string, right_longitude_string,
            limit_string)

        url = '{}?search={}'.format(url_root, search_string)

        return url

    @staticmethod
    def build_sentinel2_search_url(polygon: Polygon, start_date: str) -> str:
        """ Constructs the search url for Scihub
        :param polygon: A WKT polygon
        :param start_date: Search start date in YYYY-MM-DD format
        :return: A url string
        """
        url = 'https://scihub.copernicus.eu/dhus/search?q=\
        ingestiondate:[{date}T00:00:00.000Z TO NOW]\
         AND platformname:Sentinel-2\
         AND footprint:"Intersects({polygon})"\
         &format=json'.format(
            date=start_date,
            polygon=polygon)

        return url

    @staticmethod
    def build_sentinel2_image_url(year, month, day, utm_zone, latitude_band, grid_square) -> str:
        """ Generate a url for the Sentinel2 AWS storage
        :param year: year of the image capture
        :param month: month of the image capture
        :param day: day of the image capture
        :param utm_zone: MGRS UTM zone
        :param latitude_band: MGRS latitude band
        :param grid_square: MGRS grid square
        :return: a url string
        """
        url_root = 'http://sentinel-s2-l1c.s3.amazonaws.com/tiles'
        sequence = '0'

        folder_url = '{url_root}/{utm_zone}/{latitude_band}/{grid_square}/{year}/{month}/{day}/{sequence}'.format(
            url_root=url_root, utm_zone=utm_zone, latitude_band=latitude_band, grid_square=grid_square,
            year=year, month=month, day=day, sequence=sequence)

        return folder_url
