from pyproj import Proj, transform
from shapely.geometry import Polygon
from shapely.ops import transform as shapely_transform
from geojson import Feature
import mgrs
from functools import partial
import numpy as np
from PIL import Image as PILImage
from PIL import ImageDraw

from image.geotransform import Geotransform

WGS84_EPSG = 4326


def world_to_pixel(x: float, y: float, geotransform: Geotransform, image_height: int) -> (int, int):
    """ Transform a projected coordinates to image pixel indices
    :param x: easting/longitude
    :param y: northing/latitude
    :param geotransform: the geospatial properties of the image
    :return: x, y in pixel indices
    """

    x = np.round((x - geotransform.upper_left_x) / geotransform.pixel_width).astype(np.int)
    y = np.round((geotransform.upper_left_y - y) / geotransform.pixel_width).astype(np.int)

    return x, y


def pixel_to_world(x: int, y: int, geotransform: Geotransform) -> (float, float):
    """ Transform a pixel indices into projected coordinates
    :param x: column
    :param y: row
    :param geotransform: the geospatial properties of the image
    :return: easting/longitude, northing/latitude
    """
    x2 = (y * geotransform.pixel_width) + geotransform.upper_left_y
    y2 = (x * geotransform.pixel_width) + geotransform.upper_left_x

    return x2, y2


def polygon_to_pixel(polygon, geotransform, image_height):
    x, y = polygon.exterior.xy

    points = []
    for x, y in zip(x, y):
        x_index, y_index = world_to_pixel(x, y, geotransform=geotransform, image_height=image_height)
        points.append((x_index, y_index))

    return Polygon(points)


def transform_coordinate(x: float, y: float, in_epsg: int, out_epsg: int) -> (float, float):
    """ Tranform a coordinate to a new coordinate system
    :param x: easting/longitude
    :param y: northing/latitude
    :param in_epsg: input EPSG code
    :param out_epsg: output EPSG code
    :return: reprojected easting/longitude, northing/latitude
    """
    in_proj = Proj(init='epsg:{}'.format(in_epsg))
    out_proj = Proj(init='epsg:{}'.format(out_epsg))

    x2, y2 = transform(in_proj, out_proj, x, y)

    return x2, y2


def transform_polygon(polygon: Polygon, in_epsg: int, out_epsg: int) -> Polygon:
    """ Transform a polygon to a new coordinate system
    :param polygon: WKT Shapely polygon
    :param in_epsg: input EPSG code
    :param out_epsg: output EPSG code
    :return: reprojected polygon
    """
    projection = partial(
        transform,
        Proj(init='epsg:{}'.format(in_epsg)),
        Proj(init='epsg:{}'.format(out_epsg)))

    return shapely_transform(projection, polygon)


def wkt_to_geojson(polygon: Polygon, properties: dict=dict) -> Feature:
    """ Convert a WKT polygon to GeoJSON """
    return Feature(geometry=polygon, properties=properties)

def clip_image(image: np.array, polygon: Polygon, mask_value: float=np.nan):
    """
    Masks the pixels outside its pixel polygon.
    :param im_arr: np.array
    :param polygon: pixel_polygon
    :param mask_value: value of masked pixels
    :return: clipped image
    """
    x, y = [], []
    polygon_coords = []
    for i in polygon.exterior.coords:
        x.append(i[0])
        y.append(i[1])
        polygon_coords.append((i[0], i[1]))

    x_min, y_min = int(min(x)), int(min(y))
    x_max, y_max = int(max(x)), int(max(y))

    extent = [y_min, y_max, x_min, x_max]

    mask = _create_mask(image.shape[1], image.shape[0], polygon_coords, extent)

    if image.ndim > 2:
        im_arr_clip = image[extent[0]:extent[1], extent[2]:extent[3], :].astype(np.float)
        im_arr_clip[mask != 0, :] = mask_value

    elif image.ndim == 2:
        im_arr_clip = image[extent[0]:extent[1], extent[2]:extent[3]].astype(np.float)
        im_arr_clip[mask != 0] = mask_value

    else:
        raise Exception("Not enough dimensions in array, expected 2 or more, received {}.".format(image.ndim))

    return im_arr_clip


def _create_mask(width: int, height: int, polygon_coords: list, extent: [int]):
    """
    Create a clipper mask for clipping a polygon or extracting an image subset.
    :param width: pixel width of the image (number of columns)
    :param height: pixel height of the image (number of rows)
    :param polygon_coords: list of coordinates from clip_image function
    :param extent: extent of the coordinates from clip_image function
    :return:
    """
    mask_image = PILImage.new("L", (width, height), 1)
    ImageDraw.Draw(mask_image).polygon(polygon_coords, 0)
    mask = np.array(mask_image)

    return mask[extent[0]:extent[1], extent[2]:extent[3]]


def get_mgrs_info(wkt_polygon: Polygon) -> (str, str, str):
    """ Gets MGRS info for a polygon
    :param wkt_polygon: WKT Polygon
    :return: UTM Code, Latitude Band, Square
    """
    center = wkt_polygon.centroid
    longitude, latitude = center.x, center.y

    mgrs_converter = mgrs.MGRS()
    mgrs_code = mgrs_converter.toMGRS(latitude, longitude).decode('utf-8')

    utm_code = mgrs_code[0:2]
    latitude_band = mgrs_code[2:3]
    square = mgrs_code[3:5]

    return utm_code, latitude_band, square
