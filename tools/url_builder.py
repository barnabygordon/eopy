from shapely.geometry import Polygon
import time


class URLBuilder:
    def build_landsat8_search_url(self, polygon: Polygon, start_date, path=None, row=None, cloud_min=0, cloud_max=100, search_limit=100):
        """ Defines a Landsat-8 search url for development seed """
        url_root = 'https://api.developmentseed.org/satellites/landsat'

        if path is None and row is None:
            aoi_string = self.build_landsat8_geometry_string(polygon)
        else:
            aoi_string = "path:{}+AND+row:{}".format(path, row)

        today = time.strftime("%Y-%m-%d")

        date_string = 'acquisitionDate:[{}+TO+{}]'.format(start_date, today)
        cloud_string = 'cloudCoverFull:[{}+TO+{}]'.format(cloud_min, cloud_max)
        limit_string = 'limit={}'.format(search_limit)

        search_string = '{}+AND+{}+AND+{}&{}'.format(
            date_string, cloud_string,
            aoi_string, limit_string)

        url = '{}?search={}'.format(url_root, search_string)

        return url

    @staticmethod
    def build_landsat8_geometry_string(polygon: Polygon):
        search_bounds = polygon.bounds

        min_longitude = search_bounds[0]
        max_longitude = search_bounds[2]
        min_latitude = search_bounds[1]
        max_latitude = search_bounds[3]

        left_latitude_string = 'upperLeftCornerLatitude:[{:.2f}+TO+1000]'.format(max_latitude)
        right_latitude_string = 'lowerRightCornerLatitude:[-1000+TO+{:.2f}]'.format(min_latitude)
        left_longitude_string = 'lowerLeftCornerLongitude:[-1000+TO+{:.2f}]'.format(min_longitude)
        right_longitude_string = 'upperRightCornerLongitude:[{:.2f}+TO+1000]'.format(max_longitude)

        return "{}+AND+{}+AND+{}+AND+{}".format(left_latitude_string, right_latitude_string,
                                               left_longitude_string, right_longitude_string)

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
