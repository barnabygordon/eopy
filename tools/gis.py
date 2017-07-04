from image import Geotransform
from pyproj import Proj, transform


def world_to_pixel(x: float, y: float, geotransform: Geotransform) -> (int, int):
    x = int((x - geotransform.upper_left_x) / geotransform.pixel_width)
    y = int((y - geotransform.upper_left_y) / geotransform.pixel_width)

    return x, -y


def pixel_to_world(x: int, y: int, geotransform: Geotransform) -> (float, float):
    x2 = (y * geotransform.pixel_width) + geotransform.upper_left_y
    y2 = (x * geotransform.pixel_width) + geotransform.upper_left_x

    return x2, y2


def transform_coordinate(x: float, y: float, in_epsg: int, out_epsg: int) -> (float, float):
    in_proj = Proj(init='epsg:{}'.format(in_epsg))
    out_proj = Proj(init='epsg:{}'.format(out_epsg))

    x2, y2 = transform(in_proj, out_proj, x, y)

    return x2, y2
