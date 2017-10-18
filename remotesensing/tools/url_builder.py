from shapely.geometry import Polygon
import time


class URLBuilder:
    def build_landsat8_search_url(self, start_date=None, end_date=None, polygon: Polygon=None, path=None, row=None, cloud_min=0, cloud_max=100, search_limit=100):
        """ Defines a Landsat-8 search url for development seed
        :type end_date: str
        :type start_date: str
        :type polygon: shapely.geometry.Polygon
        :type path: str
        :type row: str
        :type cloud_min: int
        :type cloud_max: int
        :type search_limit: int
        :rtype: str
        """
        """ Defines a Landsat-8 search url for development seed """
        url_root = 'https://api.developmentseed.org/satellites/landsat'

        if all(things is not None for things in [polygon, path, row]):
            raise UserWarning("Function requires either polygon or path & row")
        elif polygon is None:
            aoi_string = "path:{}+AND+row:{}".format(path, row)
        else:
            aoi_string = self.build_landsat8_geometry_string(polygon)

        if end_date is None:
            end_date = time.strftime("%Y-%m-%d")

        if start_date is None:
            start_date = "1993-07-15"

        date_string = 'acquisitionDate:[{}+TO+{}]'.format(start_date, end_date)
        cloud_string = 'cloudCoverFull:[{}+TO+{}]'.format(cloud_min, cloud_max)
        limit_string = 'limit={}'.format(search_limit)

        search_string = '{}+AND+{}+AND+{}&{}'.format(
            date_string, cloud_string,
            aoi_string, limit_string)

        url = '{}?search={}'.format(url_root, search_string)

        return url

    @staticmethod
    def build_landsat8_geometry_string(polygon):
        """
        :type polygon: shapely.geometry.Polygon
        :rtype: str
        """
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
    def build_sentinel_search_url(polygon, start_date, platform, start_row):
        """ Constructs the search url for Scihub
        :type polygon: shapely.geometry.Polygon
        :type start_date: str
        :type platform: str
        :type start_row: int
        :rtype: str
        """
        url = 'https://scihub.copernicus.eu/dhus/search?q=\
        ingestiondate:[{date}T00:00:00.000Z TO NOW]\
         AND platformname:{platform}\
         AND footprint:"Intersects({polygon})"\
         &start={start}&rows=100&format=json'.format(
            date=start_date,
            platform=platform,
            polygon=polygon,
            start=start_row)

        return url

    @staticmethod
    def build_sentinel2_image_url(year, month, day, utm_zone, latitude_band, grid_square):
        """ Generate a url for the Sentinel2 AWS storage
        :type year: str
        :type month: str
        :type day: str
        :type utm_zone: str
        :type latitude_band: str
        :type grid_square: str
        :rtype: str
        """
        url_root = 'http://sentinel-s2-l1c.s3.amazonaws.com/tiles'
        sequence = '0'

        folder_url = '{url_root}/{utm_zone}/{latitude_band}/{grid_square}/{year}/{month}/{day}/{sequence}'.format(
            url_root=url_root, utm_zone=utm_zone, latitude_band=latitude_band, grid_square=grid_square,
            year=year, month=month, day=day, sequence=sequence)

        return folder_url
