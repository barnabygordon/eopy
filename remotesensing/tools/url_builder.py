from shapely.geometry import Polygon
from datetime import datetime


class URLBuilder:
    def build_landsat8_search_url(
            self,
            start_date: str = None, end_date: str = None,
            polygon: Polygon = None,
            path: str = None, row: str = None,
            cloud_min: int = 0, cloud_max: int = 100,
            search_limit: int = 100) -> str:

        url_root = 'https://api.developmentseed.org/satellites/landsat'

        if all(things is not None for things in [polygon, path, row]):
            raise UserWarning("Function requires either polygon or path & row")
        elif polygon is None:
            aoi_string = f"path:{path}+AND+row:{row}"
        else:
            aoi_string = self.build_landsat8_geometry_string(polygon)

        if end_date is None:
            end_date = datetime.strftime(datetime.today(), "%Y-%m-%d")

        if start_date is None:
            start_date = "1993-07-15"

        date_string = f'acquisitionDate:[{start_date}+TO+{end_date}]'
        cloud_string = f'cloudCoverFull:[{cloud_min}+TO+{cloud_max}]'
        limit_string = f'limit={search_limit}'

        search_string = f'{date_string}+AND+{cloud_string}+AND+{aoi_string}&{limit_string}'

        return f'{url_root}?search={search_string}'

    @staticmethod
    def build_landsat8_geometry_string(polygon: Polygon) -> str:

        search_bounds = polygon.bounds

        min_longitude = search_bounds[0]
        max_longitude = search_bounds[2]
        min_latitude = search_bounds[1]
        max_latitude = search_bounds[3]

        left_latitude_string = 'upperLeftCornerLatitude:[{:.2f}+TO+1000]'.format(max_latitude)
        right_latitude_string = 'lowerRightCornerLatitude:[-1000+TO+{:.2f}]'.format(min_latitude)
        left_longitude_string = 'lowerLeftCornerLongitude:[-1000+TO+{:.2f}]'.format(min_longitude)
        right_longitude_string = 'upperRightCornerLongitude:[{:.2f}+TO+1000]'.format(max_longitude)

        return f"{left_latitude_string}+AND+{right_latitude_string}+AND+{left_longitude_string}+AND+{right_longitude_string}"

    @staticmethod
    def build_sentinel_search_url(polygon: Polygon, platform: str, start_row: str, start_date: str, end_date: str) -> str:

        if start_date is None:
            start_date = "1993-07-15"
        if end_date is None:
            end_date = datetime.strftime(datetime.today(), "%Y-%m-%d")

        url = f'https://scihub.copernicus.eu/dhus/search?q=' \
              f'ingestiondate:[{start_date}T00:00:00.000Z TO {end_date}T00:00:00.000Z]' \
              f'AND platformname:{platform}' \
              f'AND footprint:"Intersects({polygon})' \
              f'&start={start_row}&rows=100&format=json'

        return url

    @staticmethod
    def build_sentinel2_image_url(year: str, month: str, day: str, utm_zone: str, latitude_band: str, grid_square: str) -> str:

        url_root = 'http://sentinel-s2-l1c.s3.amazonaws.com/tiles'
        sequence = '0'

        return f'{url_root}/{utm_zone}/{latitude_band}/{grid_square}/{year}/{month}/{day}/{sequence}'
